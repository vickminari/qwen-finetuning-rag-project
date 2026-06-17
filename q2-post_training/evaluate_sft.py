import os
os.environ["HF_TRUST_REMOTE_CODE"] = "1"
import json
import argparse
import torch
import torch.nn as nn
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from datasets import Dataset

# Template Alpaca para inferência e formatação
ALPACA_PROMPT_EVAL = """Abaixo está uma instrução que descreve uma tarefa, combinada com uma entrada que fornece mais contexto. Escreva uma resposta que complete adequadamente o pedido.

### Instrução:
{}

### Entrada:
{}

### Resposta:
"""

ALPACA_PROMPT_TRAIN = ALPACA_PROMPT_EVAL + "{}"

def parse_args():
    parser = argparse.ArgumentParser(description="Avaliação Pós-Treino SFT (Q2 & Q3)")
    parser.add_argument(
        "--model_name",
        type=str,
        default="Qwen/Qwen3.5-2B-Base",
        help="Nome ou caminho do modelo base original."
    )
    parser.add_argument(
        "--adapter_path",
        type=str,
        default="./q2_sft_model",
        help="Caminho para o adaptador LoRA SFT treinado."
    )
    parser.add_argument(
        "--dataset_path",
        type=str,
        default="perguntas_docentes_final.json",
        help="Caminho do dataset de perguntas/respostas para computar perplexidade."
    )
    parser.add_argument(
        "--benchmark_json",
        type=str,
        default="benchmark_sft.json",
        help="Arquivo JSON contendo as perguntas para avaliação qualitativa."
    )
    parser.add_argument(
        "--output_report",
        type=str,
        default="reports/sft_evaluation_report.md",
        help="Relatório em markdown com a comparação lado a lado."
    )
    parser.add_argument(
        "--output_json",
        type=str,
        default="reports/sft_evaluation.json",
        help="Arquivo JSON para salvar métricas quantitativas."
    )
    parser.add_argument(
        "--max_new_tokens",
        type=int,
        default=150,
        help="Número máximo de novos tokens a serem gerados."
    )
    parser.add_argument(
        "--max_eval_samples",
        type=int,
        default=100,
        help="Número máximo de amostras para avaliar perplexidade (None para todas)."
    )
    return parser.parse_args()

def load_model_and_tokenizer(model_name, adapter_path=None, device="cuda"):
    """
    Carrega o modelo base e opcionalmente aplica o adaptador LoRA.
    """
    dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
    
    tokenizer_path = adapter_path if adapter_path else model_name
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    print(f"📥 Carregando modelo base: {model_name}...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        dtype=dtype,
        device_map="auto",
        trust_remote_code=True
    )
    
    if adapter_path and os.path.exists(adapter_path):
        # Resolve se for checkpoint
        if not os.path.exists(os.path.join(adapter_path, "adapter_config.json")):
            checkpoints = [
                os.path.join(adapter_path, d)
                for d in os.listdir(adapter_path)
                if d.startswith("checkpoint-") and os.path.isdir(os.path.join(adapter_path, d))
            ]
            if checkpoints:
                checkpoints.sort(key=lambda x: int(x.split("-")[-1]))
                adapter_path = checkpoints[-1]
                print(f"🔄 Usando checkpoint mais recente: '{adapter_path}'")
        
        if os.path.exists(os.path.join(adapter_path, "adapter_config.json")):
            print(f"🔧 Aplicando adaptador LoRA de: {adapter_path}...")
            model = PeftModel.from_pretrained(model, adapter_path)
        else:
            print(f"⚠️  Diretório '{adapter_path}' não contém pesos válidos.")
            
    model.eval()
    return model, tokenizer

def evaluate_perplexity(model, tokenizer, dataset, device, max_samples=100):
    """
    Calcula a Perda de Entropia Cruzada e Perplexidade no dataset usando o template Alpaca.
    """
    model.eval()
    total_loss = 0.0
    total_tokens = 0
    loss_fn = nn.CrossEntropyLoss(reduction="sum")
    
    samples = dataset
    if max_samples and max_samples < len(dataset):
        samples = dataset.select(range(max_samples))
        
    print(f"🔍 Avaliando perplexidade em {len(samples)} amostras...")
    
    EOS_TOKEN = tokenizer.eos_token if tokenizer.eos_token else "<|endoftext|>"
    
    with torch.no_grad():
        for item in tqdm(samples, desc="Processando perplexidade"):
            instruction = item["instruction"]
            input_val = item.get("input", "")
            output = item["output"]
            
            # Formata a sequência completa
            full_text = ALPACA_PROMPT_TRAIN.format(instruction, input_val if input_val else "", output) + EOS_TOKEN
            
            inputs = tokenizer(full_text, return_tensors="pt").to(device)
            input_ids = inputs["input_ids"]
            
            outputs = model(input_ids)
            logits = outputs.logits
            
            # Shift de tokens
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = input_ids[..., 1:].contiguous()
            
            vocab_size = shift_logits.size(-1)
            flat_logits = shift_logits.view(-1, vocab_size)
            flat_labels = shift_labels.view(-1)
            
            loss = loss_fn(flat_logits, flat_labels)
            total_loss += loss.item()
            total_tokens += len(flat_labels)
            
    mean_loss = total_loss / total_tokens if total_tokens > 0 else 0.0
    perplexity = torch.exp(torch.tensor(mean_loss)).item()
    
    return {
        "cross_entropy_loss": mean_loss,
        "perplexity": perplexity
    }

def run_inference(model, tokenizer, instruction, input_val, device, max_new_tokens=150):
    """
    Executa a inferência para uma pergunta utilizando o formato Alpaca.
    """
    prompt = ALPACA_PROMPT_EVAL.format(instruction, input_val if input_val else "")
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    
    # Parâmetros de parada para evitar loop infinito
    terminators = [tokenizer.eos_token_id]
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.1,  # Temperatura mais baixa para respostas técnicas/exatas
            top_p=0.9,
            eos_token_id=terminators,
            pad_token_id=tokenizer.eos_token_id
        )
        
    input_length = inputs.input_ids.shape[1]
    generated_tokens = outputs[0][input_length:]
    return tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()

def prepare_benchmark(dataset_path, benchmark_path):
    """
    Prepara um arquivo de benchmark caso ele não exista, extraindo 25 perguntas
    aleatórias do próprio dataset SFT.
    """
    if os.path.exists(benchmark_path):
        print(f"📂 Benchmark encontrado em: {benchmark_path}")
        with open(benchmark_path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    print(f"⚠️  Benchmark '{benchmark_path}' não encontrado. Criando automaticamente com 25 amostras...")
    
    paths_to_try = [dataset_path, "perguntas_docentes_final.json", "perguntas_docentes.json"]
    data = None
    for path in paths_to_try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            break
            
    if not data:
        raise FileNotFoundError("Não foi possível encontrar o dataset para construir o benchmark.")
        
    # Amostrar 25 perguntas
    import random
    random.seed(42)
    benchmark_samples = random.sample(data, min(25, len(data)))
    
    # Salvar
    with open(benchmark_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_samples, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Benchmark de teste com {len(benchmark_samples)} perguntas salvo em: {benchmark_path}")
    return benchmark_samples

def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    print("=" * 80)
    print("📝 INICIANDO AVALIAÇÃO DO MODELO SFT")
    print("=" * 80)
    
    # 1. Carregar benchmark
    try:
        benchmark = prepare_benchmark(args.dataset_path, args.benchmark_json)
    except Exception as e:
        print(f"❌ Erro ao preparar/carregar benchmark: {e}")
        return

    # 2. Carregar dataset de validação para Perplexidade
    paths_to_try = [args.dataset_path, "perguntas_docentes_final.json", "perguntas_docentes.json"]
    val_dataset = None
    for path in paths_to_try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            # Fazer a mesma divisão de 10% de teste
            dataset = Dataset.from_list(raw_data)
            val_dataset = dataset.train_test_split(test_size=0.1, seed=42)["test"]
            break
            
    if val_dataset is None:
        print("⚠️  Dataset não encontrado para cálculo de perplexidade. Continuando sem perplexidade...")

    # ===== PASSO 1: Rodar Inferências no Modelo Baseline =====
    print("\n⏱️  Rodando avaliação no MODELO BASELINE (Sem SFT)...")
    baseline_answers = []
    baseline_metrics = {}
    
    try:
        model, tokenizer = load_model_and_tokenizer(args.model_name, device=device)
        
        # Calcular perplexidade baseline
        if val_dataset:
            baseline_metrics = evaluate_perplexity(model, tokenizer, val_dataset, device, args.max_eval_samples)
            
        # Inferências qualitativas
        for item in tqdm(benchmark, desc="Inferência Baseline"):
            ans = run_inference(model, tokenizer, item["instruction"], item.get("input", ""), device, args.max_new_tokens)
            baseline_answers.append(ans)
            
        del model
        torch.cuda.empty_cache()
    except Exception as e:
        print(f"❌ Erro ao rodar inferências no modelo baseline: {e}")
        return

    # ===== PASSO 2: Rodar Inferências no Modelo Ajustado (SFT) =====
    print("\n⏱️  Rodando avaliação no MODELO SFT (Com adaptador LoRA)...")
    sft_answers = []
    sft_metrics = {}
    
    if os.path.exists(args.adapter_path):
        try:
            model, tokenizer = load_model_and_tokenizer(args.model_name, adapter_path=args.adapter_path, device=device)
            
            # Calcular perplexidade SFT
            if val_dataset:
                sft_metrics = evaluate_perplexity(model, tokenizer, val_dataset, device, args.max_eval_samples)
                
            # Inferências qualitativas
            for item in tqdm(benchmark, desc="Inferência SFT"):
                ans = run_inference(model, tokenizer, item["instruction"], item.get("input", ""), device, args.max_new_tokens)
                sft_answers.append(ans)
                
            del model
            torch.cuda.empty_cache()
        except Exception as e:
            print(f"❌ Erro ao rodar inferências no modelo SFT: {e}")
            sft_answers = ["(Erro na carga do modelo SFT)"] * len(benchmark)
    else:
        print(f"\n⚠️  Diretório do adaptador SFT '{args.adapter_path}' não encontrado.")
        sft_answers = ["(Treinamento SFT ainda não foi executado)"] * len(benchmark)

    # ===== PASSO 3: Gerar Relatório de Comparação =====
    print(f"\n✍️  Gerando relatório de comparação em: {args.output_report}...")
    
    report_md = []
    report_md.append(f"# Relatório de Avaliação do Ajuste Fino Supervisionado (SFT) — Q2 & Q3\n")
    report_md.append(f"Este relatório compara as respostas fornecidas pelo modelo base original vs o modelo após o ajuste fino de instruções (SFT).\n")
    report_md.append(f"- **Modelo Base:** `{args.model_name}`")
    report_md.append(f"- **Adaptador SFT:** `{args.adapter_path}`")
    report_md.append(f"- **Total de Casos no Benchmark:** {len(benchmark)}\n")
    
    if baseline_metrics and sft_metrics:
        report_md.append(f"## 📈 Métricas Quantitativas (Split de Teste)\n")
        report_md.append(f"| Métrica | Modelo Baseline | Modelo Pós-SFT | Comparativo |")
        report_md.append(f"|---|---|---|---|")
        
        loss_diff = sft_metrics['cross_entropy_loss'] - baseline_metrics['cross_entropy_loss']
        ppl_diff = sft_metrics['perplexity'] - baseline_metrics['perplexity']
        
        report_md.append(f"| **Loss (Cross-Entropy)** | {baseline_metrics['cross_entropy_loss']:.4f} | {sft_metrics['cross_entropy_loss']:.4f} | {loss_diff:.4f} ({'MELHOROU' if loss_diff < 0 else 'PIOROU'}) |")
        report_md.append(f"| **Perplexidade (PPL)** | {baseline_metrics['perplexity']:.4f} | {sft_metrics['perplexity']:.4f} | {ppl_diff:.4f} ({'MELHOROU' if ppl_diff < 0 else 'PIOROU'}) |")
        report_md.append(f"\n---\n")

    report_md.append(f"## 📝 Avaliação Qualitativa Lado a Lado\n")
    for i, item in enumerate(benchmark):
        instruction = item["instruction"]
        input_val = item.get("input", "")
        reference = item["output"]
        base_ans = baseline_answers[i].replace("\n", " ")
        sft_ans = sft_answers[i].replace("\n", " ")
        
        report_md.append(f"### Questão {i+1}")
        report_md.append(f"**Pergunta:** {instruction}")
        if input_val:
            report_md.append(f"**Contexto (Input):** `{input_val}`")
        report_md.append(f"\n**Resposta de Referência:** *{reference}*\n")
        report_md.append(f"| Modelo | Resposta Gerada |")
        report_md.append(f"|---|---|")
        report_md.append(f"| **Baseline** | {base_ans} |")
        report_md.append(f"| **Pós-SFT (LoRA)** | {sft_ans} |")
        report_md.append(f"\n")
        report_md.append(f"--- \n")
        
    os.makedirs(os.path.dirname(args.output_report), exist_ok=True)
    with open(args.output_report, "w", encoding="utf-8") as f:
        f.write("\n".join(report_md))
        
    # Salvar métricas JSON
    metrics_json = {
        "baseline_metrics": baseline_metrics,
        "sft_metrics": sft_metrics
    }
    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(metrics_json, f, indent=4, ensure_ascii=False)
        
    print("\n" + "=" * 80)
    print(f"✅ Relatório gerado com sucesso em: {args.output_report}")
    print(f"📊 Métricas salvas em: {args.output_json}")
    print("=" * 80)

if __name__ == "__main__":
    main()
