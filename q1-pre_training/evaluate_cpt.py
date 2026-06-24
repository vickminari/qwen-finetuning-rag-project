import os
import json
import argparse
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from eval_utils import load_and_prepare_dataset, evaluate_model, run_qualitative_generation

def main():
    parser = argparse.ArgumentParser(description="Avaliação Pós-Treino (CPT) do Modelo (Q1)")
    parser.add_argument(
        "--model_name",
        type=str,
        default="Qwen/Qwen3.5-2B-Base",
        help="Nome ou caminho do modelo base Hugging Face original."
    )
    parser.add_argument(
        "--dataset_name",
        type=str,
        default="gutoportelaa/DOMPI-2025",
        help="Nome do dataset do Hugging Face. Por exemplo, 'gutoportelaa/DOMPI-2025' ou 'gutoportelaa/dom-pi-teresina-2025'."
    )
    parser.add_argument(
        "--adapter_path",
        type=str,
        default="./q1_cpt_model",
        help="Caminho para o diretório contendo o adaptador LoRA treinado e o tokenizer."
    )
    parser.add_argument(
        "--territories",
        type=str,
        nargs="+",
        default=["carnaubais"],
        help="Lista de territórios (splits) do dataset DOMPI-2025 para avaliação."
    )
    parser.add_argument(
        "--local_txt",
        type=str,
        default=None,
        help="Caminho opcional para arquivo de texto local com os diários."
    )
    parser.add_argument(
        "--max_samples",
        type=int,
        default=None,
        help="Número máximo de chunks para avaliar (deixe None para avaliar todo o dataset)."
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
    default_output_json = os.path.join(default_reports_dir, "q1_cpt_evaluation.json")

    parser.add_argument(
        "--output_json",
        type=str,
        default=default_output_json,
        help="Arquivo JSON para salvar os resultados da avaliação."
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("📊 INICIANDO AVALIAÇÃO DO MODELO COM CPT (Q1 - DEPOIS DO PRÉ-TREINO)")
    print("=" * 80)
    print(f"Modelo Base: {args.model_name}")
    print(f"Dataset: {args.dataset_name}")
    print(f"Adaptador LoRA: {args.adapter_path}")
    print(f"Dispositivo: {'GPU (CUDA)' if torch.cuda.is_available() else 'CPU'}")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # ===== PASSO 0: Resolver caminho do adaptador (final ou checkpoint) =====
    adapter_path = args.adapter_path
    if os.path.exists(adapter_path):
        if not os.path.exists(os.path.join(adapter_path, "adapter_config.json")):
            checkpoints = [
                os.path.join(adapter_path, d)
                for d in os.listdir(adapter_path)
                if d.startswith("checkpoint-") and os.path.isdir(os.path.join(adapter_path, d))
            ]
            if checkpoints:
                checkpoints.sort(key=lambda x: int(x.split("-")[-1]))
                adapter_path = checkpoints[-1]
                print(f"🔄 Nenhum adaptador final encontrado na raiz de '{args.adapter_path}'.")
                print(f"👉 Usando automaticamente o checkpoint mais recente: '{adapter_path}'")
            else:
                print(f"⚠️  Aviso: Nenhum arquivo 'adapter_config.json' ou subpasta 'checkpoint-*' encontrado em '{adapter_path}'.")
    
    # ===== PASSO 1: Carregar Tokenizer e Modelo Base =====
    print(f"\n📥 Carregando tokenizer de: {adapter_path} (ou caindo de volta para o base)...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(adapter_path, trust_remote_code=True)
    except Exception:
        tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=True)
        
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    # Carrega modelo com precisão bfloat16 ou float16
    dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
    
    print(f"📥 Carregando modelo base {args.model_name}...")
    base_model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        dtype=dtype,
        device_map="auto",
        trust_remote_code=True
    )
    
    # ===== PASSO 2: Carregar Adaptador LoRA =====
    print(f"🔧 Mesclando o adaptador LoRA de: {adapter_path}...")
    try:
        model = PeftModel.from_pretrained(base_model, adapter_path)
        print("✅ Adaptador LoRA carregado e aplicado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao carregar o adaptador LoRA: {e}")
        print("💡 Verifique se o diretório do adaptador contém o arquivo 'adapter_config.json' e os pesos do adaptador.")
        return
        
    # ===== PASSO 3: Preparar Dados =====
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
        
    # ===== PASSO 4: Rodar Avaliação Quantitativa =====
    print("\n📈 Executando avaliação quantitativa com o modelo CPT...")
    metrics = evaluate_model(
        model=model,
        tokenizer=tokenizer,
        eval_dataset=eval_dataset,
        device=device,
        batch_size=args.batch_size,
        max_samples=args.max_samples
    )
    
    # ===== PASSO 5: Rodar Avaliação Qualitativa =====
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
    
    # ===== PASSO 6: Salvar Resultados =====
    results = {
        "model_name": args.model_name,
        "adapter_path": adapter_path,
        "metrics": metrics,
        "generations": generations
    }
    
    # Garante que a pasta de destino exista
    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
        
    print("\n" + "=" * 80)
    print(f"💾 Resultados do CPT salvos com sucesso em: {args.output_json} (adaptador usado: {adapter_path})")
    print("=" * 80)
    
    # Sugestão de comparação
    baseline_json = os.path.join(default_reports_dir, "q1_baseline_evaluation.json")
    if not os.path.exists(baseline_json):
        if os.path.exists("reports/q1_baseline_evaluation.json"):
            baseline_json = "reports/q1_baseline_evaluation.json"
        elif os.path.exists("q1_baseline_evaluation.json"):
            baseline_json = "q1_baseline_evaluation.json"
        
    if os.path.exists(baseline_json):
        try:
            with open(baseline_json, "r", encoding="utf-8") as f:
                base_data = json.load(f)
            
            base_metrics = base_data.get("metrics", {})
            print("\n📊 COMPARAÇÃO RÁPIDA (Baseline vs CPT):")
            print(f"  - Perplexidade (PPL): {base_metrics.get('perplexity', 0.0):.4f}  ==>  {metrics['perplexity']:.4f} "
                  f"({'MELHOROU' if metrics['perplexity'] < base_metrics.get('perplexity', 0.0) else 'PIOROU/ESTÁVEL'})")
            print(f"  - Loss:              {base_metrics.get('cross_entropy_loss', 0.0):.4f}  ==>  {metrics['cross_entropy_loss']:.4f} "
                  f"({'MELHOROU' if metrics['cross_entropy_loss'] < base_metrics.get('cross_entropy_loss', 0.0) else 'PIOROU/ESTÁVEL'})")
            print(f"  - Acurácia Top-1:     {base_metrics.get('top_1_accuracy', 0.0)*100:.2f}%  ==>  {metrics['top_1_accuracy']*100:.2f}% "
                  f"({'MELHOROU' if metrics['top_1_accuracy'] > base_metrics.get('top_1_accuracy', 0.0) else 'PIOROU/ESTÁVEL'})")
        except Exception as e:
            print(f"\n⚠️  Não foi possível ler as métricas do baseline para comparação: {e}")

if __name__ == "__main__":
    main()
