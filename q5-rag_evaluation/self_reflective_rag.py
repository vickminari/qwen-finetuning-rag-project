import os
import json
import torch
from typing import List, Dict, Any, Literal
from typing_extensions import TypedDict
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "faiss_index")

# Lazy loaders to avoid importing delay and memory overhead on imports
_db = None
_llm = None
_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[RAG] Loading embeddings on {device}...")
        _embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3",
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": True}
        )
    return _embeddings

def get_db():
    global _db
    if _db is None:
        print("[RAG] Loading FAISS index...")
        _db = FAISS.load_local(db_path, get_embeddings(), allow_dangerous_deserialization=True)
    return _db

def get_llm():
    global _llm
    if _llm is None:
        print("[RAG] Initializing ChatOpenAI (Ollama compat) with reasoning_effort='none'...")
        # Local Ollama connection using qwen3.5:2b with disabled reasoning thinking
        _llm = ChatOpenAI(
            model="qwen3.5:2b",
            base_url="http://localhost:11434/v1",
            api_key="ollama",
            temperature=0,
            reasoning_effort="none"
        )
    return _llm

# Node functions
def grade_doc_relevance(question: str, doc_content: str) -> bool:
    llm = get_llm()
    prompt = f"""Você é um avaliador que determina a relevância de um documento para responder a uma pergunta do usuário.
Documento:
{doc_content}

Pergunta:
{question}

Determine se o documento é relevante para responder à pergunta. responda apenas com "sim" se for relevante, ou "não" se não for relevante. Não explique nada e não adicione mais palavras.
Resposta (sim/não):"""
    try:
        response = llm.invoke(prompt)
        content = response.content.strip().lower()
        print(f"Relevance grade: {content}")
        return "sim" in content
    except Exception as e:
        print(f"Error grading document: {e}")
        return True # Fallback to keeping doc if Ollama fails

def generate_answer(question: str, documents: List[Document]) -> str:
    llm = get_llm()
    context = "\n\n".join([f"Documento:\n{doc.page_content}" for doc in documents])
    
    prompt = f"""Você é um assistente acadêmico especialista nos docentes do Departamento de Computação (DC) da UFPI. Use os seguintes pedaços de contexto para responder à pergunta do usuário. Se você não souber a resposta ou se ela não puder ser deduzida do contexto, diga que não sabe. Responda de forma direta e concisa.

Contexto:
{context}

Pergunta:
{question}

Resposta:"""
    try:
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"Error generating answer: {e}")
        return "Erro de processamento local no Ollama."

def check_hallucination(documents: List[Document], generation: str) -> bool:
    llm = get_llm()
    context = "\n\n".join([doc.page_content for doc in documents])
    
    prompt = f"""Você é um avaliador que determina se uma resposta gerada está fundamentada e baseada exclusivamente no contexto fornecido.
Contexto:
{context}

Resposta gerada:
{generation}

Determine se a resposta gerada está totalmente baseada nos fatos do contexto e não introduz alucinações ou informações externas. responda apenas com "sim" se a resposta for baseada no contexto, ou "não" se a resposta contiver alucinações ou informações não presentes no contexto. Não adicione nenhuma outra palavra.
Resposta (sim/não):"""
    try:
        response = llm.invoke(prompt)
        content = response.content.strip().lower()
        print(f"Hallucination grade: {content}")
        return "sim" in content
    except Exception as e:
        print(f"Error checking hallucination: {e}")
        return True # Fallback

def check_answer_relevance(question: str, generation: str) -> bool:
    llm = get_llm()
    
    prompt = f"""Você é um avaliador que determina se uma resposta gerada responde à pergunta de forma útil e direta.
Pergunta:
{question}

Resposta gerada:
{generation}

Determine se a resposta gerada responde diretamente à pergunta feita e é útil. responda apenas com "sim" se for útil e relevante, ou "não" se não for. Não adicione nenhuma outra palavra.
Resposta (sim/não):"""
    try:
        response = llm.invoke(prompt)
        content = response.content.strip().lower()
        print(f"Answer usefulness grade: {content}")
        return "sim" in content
    except Exception as e:
        print(f"Error checking usefulness: {e}")
        return True # Fallback

# Define graph state
class GraphState(TypedDict):
    question: str
    generation: str
    documents: List[Document]
    steps: int

# Nodes
def retrieve_node(state: GraphState) -> Dict[str, Any]:
    print("\n--- [RAG NODE] RETRIEVE ---")
    question = state["question"]
    db = get_db()
    retriever = db.as_retriever(search_kwargs={"k": 4})
    documents = retriever.invoke(question)
    return {"documents": documents, "steps": state.get("steps", 0)}

def grade_documents_node(state: GraphState) -> Dict[str, Any]:
    print("\n--- [RAG NODE] GRADE DOCUMENTS ---")
    question = state["question"]
    documents = state["documents"]
    filtered_docs = []
    for idx, doc in enumerate(documents, 1):
        print(f"Grading document {idx}/{len(documents)}...")
        if grade_doc_relevance(question, doc.page_content):
            filtered_docs.append(doc)
    print(f"Kept {len(filtered_docs)} relevant documents out of {len(documents)}.")
    return {"documents": filtered_docs}

def generate_node(state: GraphState) -> Dict[str, Any]:
    print("\n--- [RAG NODE] GENERATE ---")
    question = state["question"]
    documents = state["documents"]
    generation = generate_answer(question, documents)
    return {"generation": generation, "steps": state.get("steps", 0) + 1}

def grade_generation_route(state: GraphState) -> str:
    print("\n--- [RAG ROUTER] CONDITIONAL GRADE GENERATION ---")
    question = state["question"]
    documents = state["documents"]
    generation = state["generation"]
    steps = state["steps"]
    
    if steps >= 3:
        print("Max self-reflection attempts reached. Accepting current generation.")
        return "accept"
        
    if not documents:
        print("No documents available to evaluate grounding. Accepting generation.")
        return "accept"
        
    is_grounded = check_hallucination(documents, generation)
    if not is_grounded:
        print(f"Hallucination/unsupported statement detected (Attempt {steps}). Retrying generation...")
        return "retry"
        
    is_relevant = check_answer_relevance(question, generation)
    if not is_relevant:
        print(f"Generation does not answer the question (Attempt {steps}). Retrying generation...")
        return "retry"
        
    print("Generation is grounded and relevant. Accepting.")
    return "accept"

# Build LangGraph workflow
workflow = StateGraph(GraphState)

workflow.add_node("retrieve", retrieve_node)
workflow.add_node("grade_documents", grade_documents_node)
workflow.add_node("generate", generate_node)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_edge("grade_documents", "generate")

workflow.add_conditional_edges(
    "generate",
    grade_generation_route,
    {
        "retry": "generate",
        "accept": END
    }
)

app = workflow.compile()

def run_self_reflective_rag(question: str) -> Dict[str, Any]:
    """
    Executes the Self-Reflective RAG pipeline for a given question.
    Returns a dictionary with 'generation' and 'contexts'.
    """
    initial_state = {
        "question": question,
        "generation": "",
        "documents": [],
        "steps": 0
    }
    
    print(f"\n==================== RUNNING SELF-REFLECTIVE RAG ====================")
    print(f"Question: {question}")
    
    result = app.invoke(initial_state)
    
    contexts = [doc.page_content for doc in result.get("documents", [])]
    
    return {
        "question": question,
        "generation": result.get("generation", ""),
        "contexts": contexts
    }

if __name__ == "__main__":
    # Test execution
    test_question = "Quais as áreas de atuação do professor André Soares?"
    res = run_self_reflective_rag(test_question)
    print("\nResult:")
    print("Answer:", res["generation"])
    print("Contexts retrieved count:", len(res["contexts"]))
