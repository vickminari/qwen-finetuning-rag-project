import os
import json
import argparse
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from eval_utils import load_and_prepare_dataset, evaluate_model, run_qualitative_generation

def main():
    parser = argparse.ArgumentParser(description="Avaliação Baseline do Modelo Causal LM (Q1)")
    parser.add_argument(
        "--model_name",
        type=str,
        default="Qwen/Qwen3.5-2B-Base",
        help="Nome ou caminho do modelo Hugging Face a ser avaliado."
    )
    parser.add_argument(
        "--dataset_name",
        type=str,
        default="gutoportelaa/DOMPI-2025",
        help="Nome do dataset do Hugging Face. Por exemplo, 'gutoportelaa/DOMPI-2025' ou 'gutoportelaa/dom-pi-teresina-2025'."
    )
    parser.add_argument(
        "--territories",
        type=str,
        nargs="+",
        default=["carnaubais"],
        help="Lista de territórios (splits) do dataset DOMPI-2025 a serem baixados/utilizados."
    )
    parser.add_argument(
        "--local_txt",
        type=str,
        default=None,
        help="Caminho opcional para arquivo de texto local com os diários, se não for baixar do Hugging Face."
    )
    parser.add_argument(
        "--max_samples",
        type=int,
        default=None,
        help="Número máximo de chunks (2048 tokens cada) para avaliar (deixe None para avaliar todo o dataset)."
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=1,
        help="Tamanho do lote para avaliação."
    )
    # Determina o caminho absoluto da pasta reports na raiz do projeto
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    default_reports_dir = os.path.join(project_root, "reports")
    default_output_json = os.path.join(default_reports_dir, "q1_baseline_evaluation.json")

    parser.add_argument(
        "--output_json",
        type=str,
        default=default_output_json,
        help="Arquivo JSON para salvar os resultados."
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("📊 INICIANDO AVALIAÇÃO BASELINE (Q1 - ANTES DO PRÉ-TREINO)")
    print("=" * 80)
    print(f"Modelo: {args.model_name}")
    print(f"Dataset: {args.dataset_name}")
    print(f"Dispositivo: {'GPU (CUDA)' if torch.cuda.is_available() else 'CPU'}")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # ===== PASSO 1: Carregar Tokenizer e Modelo =====
    print(f"\n📥 Carregando tokenizer e modelo {args.model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=True)
    
    # Define o token de padding se não estiver definido
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    # Carrega modelo com precisão adequada para o hardware do usuário
    # RTX 3060 / 4070 suportam bfloat16 perfeitamente
    dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
    
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        dtype=dtype,
        device_map="auto",
        trust_remote_code=True
    )
    
    # ===== PASSO 2: Preparar Dados =====
    print("\n📂 Preparando conjunto de validação...")
    try:
        dataset_split = load_and_prepare_dataset(
            tokenizer=tokenizer,
            dataset_name=args.dataset_name,
            territories=args.territories,
            local_txt_path=args.local_txt,
            split_ratio=0.1,
            max_seq_length=2048,
            seed=42,
            only_eval=True,
            max_samples=args.max_samples
        )
        eval_dataset = dataset_split["test"]
    except Exception as e:
        print(f"❌ Erro ao carregar/preparar dados: {e}")
        return
        
    # ===== PASSO 3: Rodar Avaliação Quantitativa =====
    print("\n📈 Executando avaliação quantitativa...")
    metrics = evaluate_model(
        model=model,
        tokenizer=tokenizer,
        eval_dataset=eval_dataset,
        device=device,
        batch_size=args.batch_size,
        max_samples=args.max_samples
    )
    
    # ===== PASSO 4: Rodar Avaliação Qualitativa =====
    # Define os prompts de acordo com o dataset selecionado
    if "teresina" in args.dataset_name.lower():
        prompts_teste = [
            "DECRETO Nº 045/2025\nO PREFEITO MUNICIPAL DE TERESINA, Estado do Piauí, no uso de suas atribuições, resolve: ",
            "PORTARIA Nº 012/2025\nO Secretário Municipal de Administração e Recursos Humanos de Teresina, resolve: ",
            "AVISO DE LICITAÇÃO. A Prefeitura Municipal de Teresina, torna público que realizará licitação na modalidade ",
            "Art. 1º. Fica nomeado para o cargo em comissão de Assessor Técnico da Prefeitura de Teresina o Sr. "
        ]
    else:
        prompts_teste = [
            "DECRETO Nº 012/2025\nEmenta: Abre crédito adicional suplementar no valor de ",
            "PORTARIA Nº 003/2025\nO PREFEITO MUNICIPAL DE CAMPO MAIOR, no uso de suas atribuições legais, resolve: ",
            "AVISO DE LICITAÇÃO. O Município de Carnaubais, torna público que realizará licitação na modalidade ",
            "Art. 1º. Fica nomeado para o cargo em comissão de Secretário Municipal de "
        ]
    
    generations = run_qualitative_generation(
        model=model,
        tokenizer=tokenizer,
        prompts=prompts_teste,
        device=device,
        max_new_tokens=80
    )
    
    # ===== PASSO 5: Salvar Resultados =====
    results = {
        "model_name": args.model_name,
        "metrics": metrics,
        "generations": generations
    }
    
    # Garante que a pasta de destino exista
    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
        
    print("\n" + "=" * 80)
    print(f"💾 Resultados do baseline salvos com sucesso em: {args.output_json}")
    print("=" * 80)

if __name__ == "__main__":
    main()
