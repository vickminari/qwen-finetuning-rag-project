import os
os.environ["HF_TRUST_REMOTE_CODE"] = "1"
import sys
import json
import re
import argparse
import random
import torch
import torch.nn as nn
import requests
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from datasets import Dataset

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from config import (
    TEACHERS,
    STUDENTS,
    ALPACA_PROMPT_EVAL,
    ALPACA_PROMPT_TRAIN,
    BENCHMARK_PATH,
    COT_DATASET_PATH,
    DEFAULT_OUTPUT_JSON,
    DEFAULT_OUTPUT_REPORT,
    EVAL_MAX_NEW_TOKENS,
    EVAL_MAX_SAMPLES_PPL,
    EVAL_SEED,
    OLLAMA_API_URL,
    OLLAMA_TIMEOUT,
    OLLAMA_TEMPERATURE,
    SFT_TEST_SPLIT,
    BENCHMARK_SAMPLE_SIZE,
    alpaca_to_benchmark_item,
    get_teacher,
    get_student,
    get_adapter_path,
    parse_cot_output,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Avaliação de professores e alunos — Q4 Destilação de Conhecimento"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["teacher", "student", "compare_all"],
        default="compare_all",
        help="Modo: professor (Ollama), aluno (HF) ou comparação completa",
    )
    parser.add_argument(
        "--teacher",
        type=str,
        default=None,
        choices=list(TEACHERS.keys()),
        help="Chave do professor (modo teacher ou compare_all)",
    )
    parser.add_argument(
        "--student",
        type=str,
        default=None,
        choices=list(STUDENTS.keys()),
        help="Chave do aluno (modo student ou compare_all)",
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default=None,
        help="Sobrescreve nome HF do aluno",
    )
    parser.add_argument(
        "--adapter_path",
        type=str,
        default=None,
        help="Caminho do adaptador LoRA pós-SFT",
    )
    parser.add_argument(
        "--dataset_path",
        type=str,
        default=COT_DATASET_PATH,
        help="Dataset CoT para perplexidade e construção do benchmark",
    )
    parser.add_argument(
        "--benchmark_json",
        type=str,
        default=BENCHMARK_PATH,
        help="Benchmark com campos prompt, reasoning, answer",
    )
    parser.add_argument(
        "--api_url",
        type=str,
        default=OLLAMA_API_URL,
        help="URL do Ollama para avaliação de professores",
    )
    parser.add_argument(
        "--output_report",
        type=str,
        default=DEFAULT_OUTPUT_REPORT,
        help="Relatório markdown",
    )
    parser.add_argument(
        "--output_json",
        type=str,
        default=DEFAULT_OUTPUT_JSON,
        help="Métricas em JSON",
    )
    parser.add_argument(
        "--max_new_tokens",
        type=int,
        default=EVAL_MAX_NEW_TOKENS,
        help="Tokens máximos na geração",
    )
    parser.add_argument(
        "--max_eval_samples",
        type=int,
        default=EVAL_MAX_SAMPLES_PPL,
        help="Amostras para perplexidade",
    )
    parser.add_argument(
        "--skip_baseline",
        action="store_true",
        help="Pula avaliação baseline do aluno (somente pós-SFT)",
    )
    parser.add_argument(
        "--skip_sft",
        action="store_true",
        help="Pula avaliação pós-SFT do aluno",
    )
    return parser.parse_args()


def normalize_text(text):
    """Normaliza texto para comparação de respostas."""
    text = (text or "").lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text


def prepare_benchmark(dataset_path, benchmark_path, sample_size=BENCHMARK_SAMPLE_SIZE):
    """
    Prepara benchmark com campos: prompt, input, reasoning, answer, reference_output.
    """
    if os.path.exists(benchmark_path):
        print(f"📂 Benchmark encontrado: {benchmark_path}")
        with open(benchmark_path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    print(f"⚠️  Benchmark não encontrado. Criando a partir de '{dataset_path}'...")

    paths_to_try = [dataset_path, COT_DATASET_PATH]
    data = None
    for path in paths_to_try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            break

    if not data:
        raise FileNotFoundError("Dataset CoT não encontrado para construir o benchmark.")

    random.seed(EVAL_SEED)
    samples = random.sample(data, min(sample_size, len(data)))

    benchmark = []
    for row in samples:
        benchmark.append(
            alpaca_to_benchmark_item(
                row.get("instruction", row.get("prompt", "")),
                row.get("input", ""),
                row.get("output", row.get("reference_output", "")),
            )
        )

    os.makedirs(os.path.dirname(benchmark_path) or ".", exist_ok=True)
    with open(benchmark_path, "w", encoding="utf-8") as handle:
        json.dump(benchmark, handle, indent=2, ensure_ascii=False)

    print(f"✅ Benchmark com {len(benchmark)} itens salvo em: {benchmark_path}")
    return benchmark


def load_val_dataset(dataset_path):
    """Carrega split de validação (10%) do dataset CoT."""
    paths_to_try = [dataset_path, COT_DATASET_PATH]
    for path in paths_to_try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as handle:
                raw_data = json.load(handle)
            rows = [
                {
                    "instruction": r["instruction"],
                    "input": r.get("input", ""),
                    "output": r["output"],
                }
                for r in raw_data
                if r.get("instruction") and r.get("output")
            ]
            dataset = Dataset.from_list(rows)
            return dataset.train_test_split(test_size=SFT_TEST_SPLIT, seed=42)["test"]
    return None


def load_hf_model(model_name, adapter_path=None, device="cuda"):
    """Carrega modelo HuggingFace com adaptador LoRA opcional."""
    dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16

    tokenizer_path = adapter_path if adapter_path else model_name
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"📥 Carregando modelo: {model_name}...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        dtype=dtype,
        device_map="auto",
        trust_remote_code=True,
    )

    if adapter_path and os.path.exists(adapter_path):
        resolved = adapter_path
        if not os.path.exists(os.path.join(adapter_path, "adapter_config.json")):
            checkpoints = [
                os.path.join(adapter_path, name)
                for name in os.listdir(adapter_path)
                if name.startswith("checkpoint-") and os.path.isdir(os.path.join(adapter_path, name))
            ]
            if checkpoints:
                checkpoints.sort(key=lambda path: int(path.split("-")[-1]))
                resolved = checkpoints[-1]

        if os.path.exists(os.path.join(resolved, "adapter_config.json")):
            print(f"🔧 Aplicando LoRA: {resolved}")
            model = PeftModel.from_pretrained(model, resolved)

    model.eval()
    return model, tokenizer


def evaluate_perplexity(model, tokenizer, dataset, device, max_samples=100):
    """Calcula cross-entropy loss e perplexidade no split de validação."""
    model.eval()
    total_loss = 0.0
    total_tokens = 0
    loss_fn = nn.CrossEntropyLoss(reduction="sum")

    samples = dataset
    if max_samples and max_samples < len(dataset):
        samples = dataset.select(range(max_samples))

    eos_token = tokenizer.eos_token if tokenizer.eos_token else "<|endoftext|>"

    with torch.no_grad():
        for item in tqdm(samples, desc="Perplexidade"):
            full_text = ALPACA_PROMPT_TRAIN.format(
                item["instruction"],
                item.get("input", "") or "",
                item["output"],
            ) + eos_token

            inputs = tokenizer(full_text, return_tensors="pt").to(device)
            input_ids = inputs["input_ids"]
            outputs = model(input_ids)
            logits = outputs.logits

            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = input_ids[..., 1:].contiguous()

            vocab_size = shift_logits.size(-1)
            loss = loss_fn(
                shift_logits.view(-1, vocab_size),
                shift_labels.view(-1),
            )
            total_loss += loss.item()
            total_tokens += shift_labels.numel()

    mean_loss = total_loss / total_tokens if total_tokens > 0 else 0.0
    perplexity = torch.exp(torch.tensor(mean_loss)).item()
    return {"cross_entropy_loss": mean_loss, "perplexity": perplexity}


def evaluate_topk_accuracy(model, tokenizer, benchmark, device, k_values=(1, 5)):
    """
    Calcula Top-1 e Top-5 accuracy token-level na porção de resposta (answer).
    Para cada token da resposta gold, verifica se está entre os top-k logits do modelo.
    """
    model.eval()
    topk_correct = {k: 0 for k in k_values}
    total_answer_tokens = 0
    eos_token = tokenizer.eos_token if tokenizer.eos_token else "<|endoftext|>"

    with torch.no_grad():
        for item in tqdm(benchmark, desc="Top-k accuracy"):
            prompt_text = ALPACA_PROMPT_EVAL.format(
                item["prompt"],
                item.get("input", "") or "",
            )
            answer_text = item["answer"]
            if not answer_text:
                continue

            prefix_ids = tokenizer(prompt_text, return_tensors="pt")["input_ids"].to(device)
            answer_ids = tokenizer(answer_text, add_special_tokens=False)["input_ids"]
            if not answer_ids:
                continue

            current_ids = prefix_ids.clone()
            for token_id in answer_ids:
                outputs = model(current_ids)
                next_logits = outputs.logits[0, -1, :]
                topk_indices = torch.topk(next_logits, max(k_values)).indices.tolist()

                for k in k_values:
                    if token_id in topk_indices[:k]:
                        topk_correct[k] += 1

                total_answer_tokens += 1
                next_token = torch.tensor([[token_id]], device=device)
                current_ids = torch.cat([current_ids, next_token], dim=1)

    metrics = {}
    for k in k_values:
        acc = topk_correct[k] / total_answer_tokens if total_answer_tokens else 0.0
        metrics[f"top{k}_accuracy"] = acc

    metrics["answer_tokens_evaluated"] = total_answer_tokens
    return metrics


def run_hf_inference(model, tokenizer, instruction, input_val, device, max_new_tokens):
    """Inferência Alpaca para modelos HuggingFace."""
    prompt = ALPACA_PROMPT_EVAL.format(instruction, input_val or "")
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.1,
            top_p=0.9,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id,
        )

    input_length = inputs.input_ids.shape[1]
    generated = outputs[0][input_length:]
    return tokenizer.decode(generated, skip_special_tokens=True).strip()


def call_ollama_inference(api_url, model_name, instruction, input_val, max_new_tokens):
    """Inferência via Ollama para professores."""
    base_url = api_url.rstrip("/")
    user_content = ALPACA_PROMPT_EVAL.format(instruction, input_val or "")

    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Responda em português do Brasil. "
                    "Use o formato:\n### Raciocínio:\n...\n\n### Resposta:\n..."
                ),
            },
            {"role": "user", "content": user_content},
        ],
        "stream": False,
        "options": {"temperature": OLLAMA_TEMPERATURE, "num_predict": max_new_tokens},
    }

    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json=payload,
            timeout=OLLAMA_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()["message"]["content"].strip()
    except Exception as exc:
        print(f"⚠️  Erro Ollama: {exc}")
        return ""


def evaluate_answer_match(generated_outputs, benchmark):
    """Calcula taxa de match exato normalizado na resposta final."""
    matches = 0
    total = len(benchmark)

    for generated, item in zip(generated_outputs, benchmark):
        _, pred_answer = parse_cot_output(generated)
        gold = normalize_text(item["answer"])
        pred = normalize_text(pred_answer)
        if gold and pred and (gold == pred or gold in pred or pred in gold):
            matches += 1

    return {"answer_match_rate": matches / total if total else 0.0, "matches": matches, "total": total}


def evaluate_teacher(teacher_key, benchmark, val_dataset, args):
    """Avalia um professor via Ollama."""
    _, teacher_cfg = get_teacher(teacher_key)
    model_name = teacher_cfg["ollama_name"]

    print(f"\n🎓 Avaliando professor: {teacher_cfg['display_name']}")

    generations = []
    for item in tqdm(benchmark, desc=f"Professor {teacher_key}"):
        text = call_ollama_inference(
            args.api_url,
            model_name,
            item["prompt"],
            item.get("input", ""),
            args.max_new_tokens,
        )
        generations.append(text)

    match_metrics = evaluate_answer_match(generations, benchmark)

    return {
        "model_key": teacher_key,
        "model_type": "teacher",
        "display_name": teacher_cfg["display_name"],
        "ollama_name": model_name,
        "metrics": {
            **match_metrics,
            "note": "Professores via Ollama: Top-k token requer logits HF; usa-se answer_match_rate.",
        },
        "generations": generations,
    }


def evaluate_student_phase(student_key, benchmark, val_dataset, device, args, phase, adapter_path=None):
    """Avalia aluno HuggingFace (baseline ou pós-SFT)."""
    _, student_cfg = get_student(student_key)
    model_name = args.model_name or student_cfg["hf_name"]

    label = "baseline" if phase == "baseline" else "sft"
    print(f"\n🎒 Avaliando aluno ({label}): {student_cfg['display_name']}")

    model, tokenizer = load_hf_model(
        model_name,
        adapter_path=adapter_path if phase == "sft" else None,
        device=device,
    )

    metrics = {}
    if val_dataset is not None:
        metrics.update(evaluate_perplexity(model, tokenizer, val_dataset, device, args.max_eval_samples))

    metrics.update(evaluate_topk_accuracy(model, tokenizer, benchmark, device))

    generations = []
    for item in tqdm(benchmark, desc=f"Aluno {label}"):
        text = run_hf_inference(
            model,
            tokenizer,
            item["prompt"],
            item.get("input", ""),
            device,
            args.max_new_tokens,
        )
        generations.append(text)

    match_metrics = evaluate_answer_match(generations, benchmark)
    metrics.update(match_metrics)

    del model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return {
        "model_key": student_key,
        "model_type": "student",
        "phase": phase,
        "display_name": student_cfg["display_name"],
        "hf_name": model_name,
        "adapter_path": adapter_path,
        "metrics": metrics,
        "generations": generations,
    }


def _fmt_metric(value, digits=4):
    if value is None:
        return "—"
    return f"{value:.{digits}f}"


def write_report(all_results, benchmark, args):
    """Gera relatório markdown comparativo."""
    lines = [
        "# Relatório de Avaliação — Q4 Destilação de Conhecimento\n",
        "Comparação de professores (Ollama) e alunos (HF) antes e depois do SFT.\n",
        f"- **Benchmark:** `{args.benchmark_json}` ({len(benchmark)} itens)",
        f"- **Dataset:** `{args.dataset_path}`\n",
        "## Métricas Quantitativas\n",
        "| Modelo | Tipo | Fase | Loss | PPL | Top-1 | Top-5 | Answer Match |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]

    for result in all_results:
        m = result["metrics"]
        lines.append(
            f"| {result.get('display_name', result['model_key'])} "
            f"| {result.get('model_type', '-')} "
            f"| {result.get('phase', '-')} "
            f"| {_fmt_metric(m.get('cross_entropy_loss'))} "
            f"| {_fmt_metric(m.get('perplexity'))} "
            f"| {_fmt_metric(m.get('top1_accuracy'))} "
            f"| {_fmt_metric(m.get('top5_accuracy'))} "
            f"| {_fmt_metric(m.get('answer_match_rate'))} |"
        )

    lines.append("\n---\n")
    lines.append("## Avaliação Qualitativa (amostra)\n")

    sample_count = min(10, len(benchmark))
    for i in range(sample_count):
        item = benchmark[i]
        lines.append(f"### Questão {i + 1}")
        lines.append(f"**Prompt:** {item['prompt']}")
        if item.get("input"):
            lines.append(f"**Input:** `{item['input']}`")
        lines.append(f"\n**Raciocínio de referência:** *{item['reasoning'][:300]}...*\n")
        lines.append(f"**Resposta de referência:** *{item['answer']}*\n")
        lines.append("| Modelo | Resposta gerada |")
        lines.append("|---|---|")

        for result in all_results:
            gen = result["generations"][i].replace("\n", " ") if i < len(result["generations"]) else "—"
            label = result.get("display_name", result["model_key"])
            if result.get("phase"):
                label += f" ({result['phase']})"
            lines.append(f"| {label} | {gen[:500]} |")

        lines.append("\n---\n")

    os.makedirs(os.path.dirname(args.output_report) or ".", exist_ok=True)
    with open(args.output_report, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print("=" * 80)
    print("📊 AVALIAÇÃO — Q4 DESTILAÇÃO DE CONHECIMENTO")
    print("=" * 80)

    try:
        benchmark = prepare_benchmark(args.dataset_path, args.benchmark_json)
    except Exception as exc:
        print(f"❌ Erro ao preparar benchmark: {exc}")
        return

    val_dataset = load_val_dataset(args.dataset_path)
    all_results = []

    if args.mode in ("teacher", "compare_all"):
        teachers_to_eval = list(TEACHERS.keys()) if args.mode == "compare_all" else [get_teacher(args.teacher)[0]]
        for teacher_key in teachers_to_eval:
            try:
                result = evaluate_teacher(teacher_key, benchmark, val_dataset, args)
                all_results.append(result)
            except Exception as exc:
                print(f"❌ Erro ao avaliar professor {teacher_key}: {exc}")

    if args.mode in ("student", "compare_all"):
        student_key = get_student(args.student)[0] if args.student else get_student()[0]
        adapter_path = args.adapter_path or get_adapter_path(student_key)

        if not args.skip_baseline:
            try:
                result = evaluate_student_phase(
                    student_key, benchmark, val_dataset, device, args, phase="baseline"
                )
                all_results.append(result)
            except Exception as exc:
                print(f"❌ Erro baseline do aluno: {exc}")

        if not args.skip_sft and os.path.exists(adapter_path):
            try:
                result = evaluate_student_phase(
                    student_key,
                    benchmark,
                    val_dataset,
                    device,
                    args,
                    phase="sft",
                    adapter_path=adapter_path,
                )
                all_results.append(result)
            except Exception as exc:
                print(f"❌ Erro pós-SFT do aluno: {exc}")
        elif not args.skip_sft:
            print(f"⚠️  Adaptador não encontrado em '{adapter_path}'. Pulando avaliação pós-SFT.")

    write_report(all_results, benchmark, args)

    metrics_export = []
    for result in all_results:
        export_item = {k: v for k, v in result.items() if k != "generations"}
        export_item["sample_generations"] = result["generations"][:5]
        metrics_export.append(export_item)

    os.makedirs(os.path.dirname(args.output_json) or ".", exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as handle:
        json.dump({"results": metrics_export, "benchmark_size": len(benchmark)}, handle, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print(f"✅ Relatório: {args.output_report}")
    print(f"📊 Métricas JSON: {args.output_json}")
    print("=" * 80)


if __name__ == "__main__":
    main()
