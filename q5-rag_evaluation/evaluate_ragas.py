import os
import json
import torch
from datasets import Dataset
from ragas import evaluate
from ragas.run_config import RunConfig
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings

def run_evaluation():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    no_rag_path = os.path.join(script_dir, "results_no_rag.json")
    with_rag_path = os.path.join(script_dir, "results_with_rag.json")
    report_path = os.path.abspath(os.path.join(script_dir, "../reports/q5_ragas_evaluation.json"))
    
    # 1. Check if files exist
    if not os.path.exists(no_rag_path) or not os.path.exists(with_rag_path):
        raise FileNotFoundError("Results files not found. Please run generate_results.py first.")
        
    print(f"Loading results...")
    with open(no_rag_path, "r", encoding="utf-8") as f:
        no_rag_results = json.load(f)
    with open(with_rag_path, "r", encoding="utf-8") as f:
        with_rag_results = json.load(f)
        
    # 2. Configure RAGAS LLM and Embeddings using local models
    model_name = "qwen3.5:9b"
    print(f"Initializing local LLM ({model_name}) as Ragas judge...")
    # ChatOpenAI connects to Ollama's compatibility endpoint. qwen3.5:2b is used here to fit in VRAM.
    judge_llm = ChatOpenAI(
        model=model_name,
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        temperature=0,
        reasoning_effort="none"
    )
    ragas_llm = LangchainLLMWrapper(judge_llm, bypass_n=True)
    
    print("Initializing local Embeddings (BAAI/bge-m3) for Ragas...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    embeddings_model = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True}
    )
    ragas_embeddings = LangchainEmbeddingsWrapper(embeddings_model)
    
    metrics = [
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall
    ]
    
    # Configure execution limits to prevent local Ollama from timing out
    run_config = RunConfig(
        max_workers=1,      # Process requests one-by-one to prevent GPU overloading
        timeout=180,        # 180 seconds timeout per request
        max_retries=10
    )
    
    # 3. Format datasets for Ragas
    # Ragas expects: question, answer, contexts, ground_truth
    # Contexts must be a list of lists of strings.
    
    # Format No-RAG dataset
    no_rag_data = {
        "question": [item["question"] for item in no_rag_results],
        "answer": [item["answer"] for item in no_rag_results],
        "contexts": [item["contexts"] if item["contexts"] else [""] for item in no_rag_results],
        "ground_truth": [item["ground_truth"] for item in no_rag_results]
    }
    
    # Format With-RAG dataset
    with_rag_data = {
        "question": [item["question"] for item in with_rag_results],
        "answer": [item["answer"] for item in with_rag_results],
        "contexts": [item["contexts"] if item["contexts"] else [""] for item in with_rag_results],
        "ground_truth": [item["ground_truth"] for item in with_rag_results]
    }
    
    no_rag_ds = Dataset.from_dict(no_rag_data)
    with_rag_ds = Dataset.from_dict(with_rag_data)
    
    # 4. Evaluate No-RAG
    print("\nEvaluating No-RAG configuration...")
    no_rag_eval = evaluate(
        dataset=no_rag_ds,
        metrics=metrics,
        llm=ragas_llm,
        embeddings=ragas_embeddings,
        run_config=run_config,
        raise_exceptions=False
    )
    print("No-RAG Evaluation finished:", no_rag_eval)
    
    # 5. Evaluate With-RAG
    print("\nEvaluating With-RAG configuration...")
    with_rag_eval = evaluate(
        dataset=with_rag_ds,
        metrics=metrics,
        llm=ragas_llm,
        embeddings=ragas_embeddings,
        run_config=run_config,
        raise_exceptions=False
    )
    print("With-RAG Evaluation finished:", with_rag_eval)
    
    # Save the evaluations
    report = {
        "no_rag": {
            "scores": no_rag_eval._repr_dict,
            "raw": no_rag_results
        },
        "with_rag": {
            "scores": with_rag_eval._repr_dict,
            "raw": with_rag_results
        }
    }
    
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nSaved RAGAS evaluation report to: {report_path}")

if __name__ == "__main__":
    run_evaluation()
