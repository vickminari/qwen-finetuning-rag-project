import os
import json

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    source_path = os.path.abspath(os.path.join(script_dir, "../perguntas_docentes.json"))
    dest_path = os.path.abspath(os.path.join(script_dir, "benchmark_rag_30.json"))
    
    print(f"Reading SFT questions from: {source_path}")
    with open(source_path, "r", encoding="utf-8") as f:
        questions = json.load(f)
        
    print(f"Total questions available: {len(questions)}")
    
    # Let's select 30 questions. We can select every Nth question to get a diverse distribution.
    n = len(questions)
    step = n // 30
    selected = [questions[i * step] for i in range(30)]
    
    # Let's save the selected questions
    print(f"Saving 30 selected questions to: {dest_path}")
    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)
        
    print("Benchmark prepared successfully!")

if __name__ == "__main__":
    main()
