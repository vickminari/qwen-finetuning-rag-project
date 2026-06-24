import os
import json
import torch
from tqdm import tqdm
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    jsonl_path = os.path.abspath(os.path.join(script_dir, "../../../dados_docentes/docentesDC/docentesDC.jsonl"))
    db_path = os.path.abspath(os.path.join(script_dir, "faiss_index"))
    
    print(f"Loading documents from {jsonl_path}...")
    documents = []
    
    # Check if the file exists
    if not os.path.exists(jsonl_path):
        raise FileNotFoundError(f"Source file not found at: {jsonl_path}")
        
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                text = data.get("text", "")
                nome_professor = data.get("nome_professor", "Desconhecido")
                
                # Only load if text is not empty
                if text.strip():
                    metadata = {
                        "nome_professor": nome_professor,
                        "line": line_num
                    }
                    documents.append(Document(page_content=text, metadata=metadata))
            except json.JSONDecodeError as e:
                print(f"Warning: JSON decode error at line {line_num}: {e}")
                
    print(f"Loaded {len(documents)} documents.")
    
    print("Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)
    print(f"Total chunks created: {len(docs)}")
    
    # Configure device (GPU by default, can be changed to 'cpu')
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using PyTorch device for embeddings: {device}")
    
    print("Loading HuggingFaceEmbeddings with model BAAI/bge-m3...")
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True}
    )
    
    print("Generating embeddings in batches...")
    texts = [doc.page_content for doc in docs]
    metadatas = [doc.metadata for doc in docs]
    
    # Set batch size. 128 is efficient for GPU; for CPU, a size of 64 or 32 is also fine.
    batch_size = 128
    all_embeddings = []
    
    # We use tqdm here to show a progress bar in the terminal
    for i in tqdm(range(0, len(texts), batch_size), desc="Embedding chunks"):
        batch_texts = texts[i:i+batch_size]
        try:
            batch_embeds = embeddings.embed_documents(batch_texts)
            all_embeddings.extend(batch_embeds)
        except Exception as e:
            print(f"\n[ERROR] Failed to embed batch starting at index {i}: {e}")
            print("[TIP] If this is a CUDA Out of Memory or paging error, edit the script to use device = 'cpu'.")
            raise e
            
    print("Building FAISS index from pre-computed embeddings...")
    text_embeddings = list(zip(texts, all_embeddings))
    db = FAISS.from_embeddings(text_embeddings, embeddings, metadatas=metadatas)
    
    print(f"Saving vector store locally to: {db_path}")
    db.save_local(db_path)
    print("Vector store indexing complete!")

if __name__ == "__main__":
    main()
