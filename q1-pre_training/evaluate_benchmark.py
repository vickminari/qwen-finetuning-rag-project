import os
import json
import argparse
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from tqdm import tqdm

def load_model_and_tokenizer(model_name, adapter_path=None, device="cuda"):
    """
    Carrega o modelo base e aplica opcionalmente os adaptadores LoRA.
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
    
    if adapter_path:
        print(f"🔧 Aplicando adaptador LoRA de: {adapter_path}...")
        model = PeftModel.from_pretrained(model, adapter_path)
        
    model.eval()
    return model, tokenizer

def run_inference(model, tokenizer, prompt, device, max_new_tokens=100):
    """
    Gera texto a partir de um prompt e retorna a resposta gerada.
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.3, # Menor temperatura para respostas mais factuais
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )
    # Retorna apenas o texto gerado após o prompt
    input_length = inputs.input_ids.shape[1]
    generated_tokens = outputs[0][input_length:]
    return tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()

def main():
    parser = argparse.ArgumentParser(description="Executa o benchmark Q&A de Q1 para Baseline vs CPT")
    parser.add_argument(
        "--model_name",
        type=str,
        default="Qwen/Qwen3.5-2B-Base",
        help="Nome ou caminho do modelo base."
    )
    parser.add_argument(
        "--adapter_path",
        type=str,
        default="./q1_cpt_model",
        help="Caminho para o adaptador LoRA treinado em Q1."
    )
    parser.add_argument(
        "--benchmark_json",
        type=str,
        default="benchmark_q1.json",
        help="Caminho para o arquivo JSON contendo as perguntas do benchmark."
    )
    # Determina o caminho absoluto da pasta reports na raiz do projeto
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    default_reports_dir = os.path.join(project_root, "reports")
    default_output_report = os.path.join(default_reports_dir, "benchmark_comparison_report.md")

    parser.add_argument(
        "--output_report",
        type=str,
        default=default_output_report,
        help="Caminho do arquivo Markdown para salvar a comparação detalhada."
    )
    parser.add_argument(
        "--max_new_tokens",
        type=int,
        default=100,
        help="Número máximo de tokens a serem gerados para cada resposta."
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("📝 EXECUTANDO BENCHMARK DE PERGUNTAS E RESPOSTAS (Q1)")
    print("=" * 80)
    
    # Verifica se o arquivo do benchmark existe
    if not os.path.exists(args.benchmark_json):
        print(f"❌ Arquivo de benchmark '{args.benchmark_json}' não encontrado!")
        print("💡 Criando um exemplo 'benchmark_q1.json' com questões de demonstração...")
        exemplo = [
            {
                "id": 1,
                "question": "De acordo com os diários, qual município piauiense realizou o pregão eletrônico para aquisição de medicamentos em janeiro de 2025?",
                "reference": "O município de Campo Maior realizou pregão eletrônico para aquisição de medicamentos em janeiro de 2025."
            },
            {
                "id": 2,
                "question": "Qual o limite de VRAM e configuração recomendada no planejamento para treinar o Qwen3.5-2B-Base?",
                "reference": "O limite é de 8GB de VRAM (RTX 4070/3060) usando bf16 LoRA com rank 256, otimizador adamw_8bit e gradient_accumulation_steps=8."
            }
        ]
        with open(args.benchmark_json, "w", encoding="utf-8") as f:
            json.dump(exemplo, f, indent=4, ensure_ascii=False)
        print(f"✅ Exemplo criado em: {args.benchmark_json}. Por favor, edite-o com as suas pelo menos 25 perguntas do benchmark.")
        return

    # Carrega perguntas
    with open(args.benchmark_json, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
        
    print(f"📋 Carregadas {len(benchmark)} perguntas do benchmark.")
    
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
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # ===== PASSO 1: Rodar Inferências no Modelo Baseline =====
    print("\n⏱️  Rodando inferências no MODELO BASELINE (sem CPT)...")
    baseline_answers = []
    try:
        model, tokenizer = load_model_and_tokenizer(args.model_name, device=device)
        for item in tqdm(benchmark, desc="Baseline"):
            # Suporta chaves em inglês ou português
            q_text = item.get("question", item.get("pergunta"))
            if not q_text:
                raise KeyError("O item do benchmark não possui a chave 'question' ou 'pergunta'.")
            prompt = f"Pergunta: {q_text}\nResposta:"
            ans = run_inference(model, tokenizer, prompt, device, args.max_new_tokens)
            baseline_answers.append(ans)
            
        # Limpa cache de memória
        del model
        torch.cuda.empty_cache()
    except Exception as e:
        print(f"❌ Erro ao rodar inferências no modelo baseline: {e}")
        return

    # ===== PASSO 2: Rodar Inferências no Modelo CPT =====
    cpt_answers = []
    if os.path.exists(adapter_path):
        print("\n⏱️  Rodando inferências no MODELO CPT (com adaptador LoRA)...")
        try:
            model, tokenizer = load_model_and_tokenizer(args.model_name, adapter_path=adapter_path, device=device)
            for item in tqdm(benchmark, desc="Modelo CPT"):
                q_text = item.get("question", item.get("pergunta"))
                prompt = f"Pergunta: {q_text}\nResposta:"
                ans = run_inference(model, tokenizer, prompt, device, args.max_new_tokens)
                cpt_answers.append(ans)
                
            del model
            torch.cuda.empty_cache()
        except Exception as e:
            print(f"❌ Erro ao carregar/rodar inferências no modelo CPT: {e}")
            cpt_answers = ["Erro ao carregar modelo CPT"] * len(benchmark)
    else:
        print(f"\n⚠️  Diretório do adaptador CPT '{adapter_path}' não encontrado.")
        print("As respostas do modelo CPT serão preenchidas com marcadores vazios.")
        cpt_answers = ["(Treinamento CPT ainda não foi realizado)"] * len(benchmark)

    # ===== PASSO 3: Gerar Relatório de Comparação =====
    print(f"\n✍️  Gerando relatório de comparação em: {args.output_report}...")
    
    report_md = []
    report_md.append(f"# Relatório de Comparação de Benchmark Q&A — Q1")
    report_md.append(f"Este relatório compara as respostas geradas pelo modelo base original vs o modelo após pré-treino continuado (CPT).\n")
    report_md.append(f"- **Modelo Base:** `{args.model_name}`")
    report_md.append(f"- **Adaptador CPT:** `{adapter_path}`")
    report_md.append(f"- **Total de Questões:** {len(benchmark)}\n")
    report_md.append(f"--- \n")
    
    for i, item in enumerate(benchmark):
        q_id = item.get("id", i + 1)
        question = item.get("question", item.get("pergunta"))
        ref = item.get("reference", item.get("resposta", item.get("answer")))
        base_ans = baseline_answers[i]
        cpt_ans = cpt_answers[i]
        
        report_md.append(f"## Questão {q_id}")
        report_md.append(f"**Pergunta:** {question}\n")
        report_md.append(f"**Resposta de Referência:** *{ref}*\n")
        report_md.append(f"| Modelo | Resposta Gerada |")
        report_md.append(f"|---|---|")
        # Escapar quebras de linha para exibição correta na tabela markdown
        base_ans_clean = base_ans.replace("\n", " ")
        cpt_ans_clean = cpt_ans.replace("\n", " ")
        report_md.append(f"| **Baseline** | {base_ans_clean} |")
        report_md.append(f"| **CPT (rsLoRA)** | {cpt_ans_clean} |")
        report_md.append(f"\n")
        report_md.append(f"--- \n")
        
    # Garante que a pasta de destino exista
    os.makedirs(os.path.dirname(args.output_report), exist_ok=True)
    with open(args.output_report, "w", encoding="utf-8") as f:
        f.write("\n".join(report_md))
        
    print("\n" + "=" * 80)
    print(f"✅ Relatório do benchmark gerado com sucesso em: {args.output_report}")
    print("=" * 80)

if __name__ == "__main__":
    main()
