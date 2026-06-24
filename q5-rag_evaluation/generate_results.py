import os
import json
from langchain_openai import ChatOpenAI
from self_reflective_rag import run_self_reflective_rag

def generate_no_rag(questions):
    print("\n==================== RUNNING NO-RAG GENERATION ====================")
    llm = ChatOpenAI(
        model="qwen3.5:2b",
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        temperature=0,
        reasoning_effort="none"
    )
    
    results = []
    for idx, item in enumerate(questions, 1):
        question = item["instruction"]
        ground_truth = item["output"]
        
        print(f"[{idx}/{len(questions)}] No-RAG Question: {question}")
        
        prompt = f"""Você é um assistente acadêmico especialista nos docentes do Departamento de Computação (DC) da UFPI. Responda diretamente e de forma concisa à pergunta do usuário.

Pergunta: {question}

Resposta:"""
        
        try:
            response = llm.invoke(prompt)
            answer = response.content.strip()
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            answer = "Erro de processamento no Ollama."
            
        results.append({
            "question": question,
            "answer": answer,
            "contexts": [],
            "ground_truth": ground_truth
        })
        
    return results

def generate_with_rag(questions):
    print("\n==================== RUNNING WITH-RAG GENERATION ====================")
    results = []
    for idx, item in enumerate(questions, 1):
        question = item["instruction"]
        ground_truth = item["output"]
        
        print(f"[{idx}/{len(questions)}] With-RAG Question: {question}")
        
        try:
            rag_output = run_self_reflective_rag(question)
            answer = rag_output["generation"]
            contexts = rag_output["contexts"]
        except Exception as e:
            print(f"Error running Self-Reflective RAG: {e}")
            answer = "Erro de processamento no pipeline RAG."
            contexts = []
            
        results.append({
            "question": question,
            "answer": answer,
            "contexts": contexts,
            "ground_truth": ground_truth
        })
        
    return results

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    benchmark_path = os.path.join(script_dir, "benchmark_rag_30.json")
    no_rag_path = os.path.join(script_dir, "results_no_rag.json")
    with_rag_path = os.path.join(script_dir, "results_with_rag.json")
    
    if not os.path.exists(benchmark_path):
        raise FileNotFoundError(f"Benchmark file not found at {benchmark_path}. Run prepare_benchmark.py first.")
        
    with open(benchmark_path, "r", encoding="utf-8") as f:
        questions = json.load(f)
        
    # 1. Generate No-RAG results
    no_rag_results = generate_no_rag(questions)
    with open(no_rag_path, "w", encoding="utf-8") as f:
        json.dump(no_rag_results, f, ensure_ascii=False, indent=2)
    print(f"Saved No-RAG results to {no_rag_path}")
    
    # 2. Generate With-RAG results
    with_rag_results = generate_with_rag(questions)
    with open(with_rag_path, "w", encoding="utf-8") as f:
        json.dump(with_rag_results, f, ensure_ascii=False, indent=2)
    print(f"Saved With-RAG results to {with_rag_path}")
    
    print("\nResults generation completed successfully!")

if __name__ == "__main__":
    main()
