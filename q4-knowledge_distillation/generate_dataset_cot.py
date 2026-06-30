import os
import sys
import json
import random
import time
import argparse
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from config import (
    TEACHERS,
    DATASET_HF_NAME,
    DATASET_SPLIT,
    DATASET_SEED,
    DOLLY_INSTRUCTION_FIELD,
    DOLLY_CONTEXT_FIELD,
    DOLLY_RESPONSE_FIELD,
    DOLLY_CATEGORY_FIELD,
    COT_DATASET_PATH,
    COT_CHECKPOINT_PATH,
    COT_TARGET_COUNT,
    OLLAMA_API_URL,
    OLLAMA_TIMEOUT,
    OLLAMA_TEMPERATURE,
    format_cot_output,
    get_teacher,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Gerador de dataset CoT (Q4 - Destilação) usando professores via Ollama"
    )
    parser.add_argument(
        "--teacher",
        type=str,
        default=None,
        choices=list(TEACHERS.keys()),
        help="Chave do professor em config.TEACHERS (ex: qwen3-14b, gemma3-12b)",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=DATASET_HF_NAME,
        help="Repositório Hugging Face ou caminho local (.json / .jsonl)",
    )
    parser.add_argument(
        "--api_url",
        type=str,
        default=OLLAMA_API_URL,
        help="URL base do Ollama (padrão: http://localhost:11434)",
    )
    parser.add_argument(
        "--target_count",
        type=int,
        default=COT_TARGET_COUNT,
        help="Quantidade total de exemplos CoT a gerar",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=COT_DATASET_PATH,
        help="Arquivo JSON final com o dataset Alpaca + CoT",
    )
    parser.add_argument(
        "--checkpoint_file",
        type=str,
        default=COT_CHECKPOINT_PATH,
        help="Arquivo JSONL para salvar progresso incremental",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DATASET_SEED,
        help="Semente aleatória para amostragem",
    )
    parser.add_argument(
        "--categories",
        type=str,
        nargs="*",
        default=None,
        help="Filtrar categorias do Dolly (ex: closed_qa open_qa). Vazio = todas.",
    )
    return parser.parse_args()


def load_dolly_dataset(dataset_source, categories=None):
    """
    Carrega o dataset Databricks Dolly-15k via Hugging Face ou arquivo local.
    Retorna lista de dicts com instruction, context, response, category.
    """
    if os.path.exists(dataset_source):
        return load_local_dataset(dataset_source, categories)

    try:
        print(f"📥 Carregando dataset do Hugging Face '{dataset_source}'...")
        from datasets import load_dataset

        dataset = load_dataset(dataset_source, split=DATASET_SPLIT)
        rows = []
        for row in dataset:
            item = {
                "instruction": row.get(DOLLY_INSTRUCTION_FIELD, "").strip(),
                "context": row.get(DOLLY_CONTEXT_FIELD, "") or "",
                "response": row.get(DOLLY_RESPONSE_FIELD, "").strip(),
                "category": row.get(DOLLY_CATEGORY_FIELD, "general").strip(),
            }
            if item["instruction"] and item["response"]:
                rows.append(item)
        print(f"✅ Dataset carregado! Registros válidos: {len(rows)}")
    except Exception as exc:
        raise RuntimeError(
            f"Não foi possível carregar '{dataset_source}' do Hugging Face: {exc}"
        ) from exc

    if categories:
        categories_lower = {c.lower() for c in categories}
        rows = [r for r in rows if r["category"].lower() in categories_lower]
        print(f"🔎 Após filtro de categorias {categories}: {len(rows)} registros")

    return rows


def load_local_dataset(path, categories=None):
    """Carrega dataset local JSON ou JSONL no formato Dolly."""
    print(f"📂 Carregando dataset local: {path}")
    rows = []

    if path.endswith(".jsonl"):
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
    elif path.endswith(".json"):
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(f)
            rows = data if isinstance(data, list) else data.get("data", [])
    else:
        raise ValueError("Formato local não suportado. Use .json ou .jsonl.")

    normalized = []
    for row in rows:
        instruction = row.get("instruction") or row.get("prompt", "")
        context = row.get("context") or row.get("input", "") or ""
        response = row.get("response") or row.get("output", "") or row.get("answer", "")
        category = row.get("category", "general")
        if str(instruction).strip() and str(response).strip():
            normalized.append({
                "instruction": str(instruction).strip(),
                "context": str(context).strip() if context else "",
                "response": str(response).strip(),
                "category": str(category).strip(),
            })

    if categories:
        categories_lower = {c.lower() for c in categories}
        normalized = [r for r in normalized if r["category"].lower() in categories_lower]

    print(f"✅ Carregados {len(normalized)} registros locais.")
    return normalized


def call_ollama_teacher(api_url, model_name, system_prompt, user_prompt):
    """
    Envia requisição ao Ollama e retorna o conteúdo gerado.
    Tenta API compatível OpenAI (/v1/chat/completions) e cai para /api/chat nativo.
    """
    base_url = api_url.rstrip("/")

    try:
        from openai import OpenAI

        openai_base = base_url if base_url.endswith("/v1") else f"{base_url}/v1"
        client = OpenAI(base_url=openai_base, api_key="ollama")
        response = client.chat.completions.create(
            model=model_name,
            temperature=OLLAMA_TEMPERATURE,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            extra_body={"reasoning_effort": "none"},
        )
        return response.choices[0].message.content
    except Exception:
        pass

    endpoint = f"{base_url}/v1/chat/completions"
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "response_format": {"type": "json_object"},
        "temperature": OLLAMA_TEMPERATURE,
    }

    try:
        response = requests.post(endpoint, json=payload, timeout=OLLAMA_TIMEOUT)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception:
        native_endpoint = f"{base_url}/api/chat"
        native_payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": OLLAMA_TEMPERATURE},
        }
        try:
            response = requests.post(native_endpoint, json=native_payload, timeout=OLLAMA_TIMEOUT)
            response.raise_for_status()
            return response.json()["message"]["content"]
        except Exception as exc:
            print(f"❌ Falha ao chamar Ollama: {exc}")
            return None


def parse_llm_json(raw_text):
    """Analisa a saída JSON do LLM, tolerando blocos markdown."""
    if not raw_text:
        return None

    clean_text = raw_text.strip()
    if clean_text.startswith("```"):
        lines = clean_text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        clean_text = "\n".join(lines).strip()

    try:
        data = json.loads(clean_text)
        if isinstance(data, dict):
            return data
    except Exception as exc:
        print(f"⚠️  Erro ao decodificar JSON: {exc}. Trecho:\n{raw_text[:200]}...")

    return None


def build_teacher_prompts(sample):
    """Monta prompts para o professor gerar raciocínio CoT + resposta."""
    instruction = sample["instruction"]
    context = sample["context"]
    reference = sample["response"]

    system_prompt = (
        "Você é um modelo professor especialista em raciocínio passo a passo (Chain-of-Thought). "
        "Gere explicações claras, técnicas e autocontidas em português do Brasil."
    )

    context_block = ""
    if context:
        context_block = f"\n\nContexto adicional:\n\"\"\"\n{context}\n\"\"\""

    user_prompt = (
        f"Pergunta:\n{instruction}"
        f"{context_block}\n\n"
        f"Resposta de referência (use como guia, mas melhore com raciocínio explícito):\n"
        f"\"\"\"\n{reference}\n\"\"\"\n\n"
        f"Sua tarefa:\n"
        f"1. Elabore um raciocínio passo a passo (Chain-of-Thought) que leve logicamente à resposta.\n"
        f"2. Forneça a resposta final concisa e correta.\n"
        f"3. NÃO mencione 'dataset', 'Dolly', 'referência' ou 'texto acima'.\n"
        f"4. Responda SOMENTE com JSON válido neste formato:\n"
        f"{{\n"
        f'  "reasoning": "raciocínio passo a passo...",\n'
        f'  "answer": "resposta final concisa..."\n'
        f"}}\n"
    )

    return system_prompt, user_prompt


def main():
    args = parse_args()
    random.seed(args.seed)

    teacher_key, teacher_cfg = get_teacher(args.teacher)
    model_name = teacher_cfg["ollama_name"]

    print("=" * 80)
    print("🧠 GERADOR DE DATASET CoT — DESTILAÇÃO DE CONHECIMENTO (Q4)")
    print("=" * 80)
    print(f"Professor: {teacher_cfg['display_name']} ({model_name})")
    print(f"Dataset: {args.dataset}")
    print(f"Meta de exemplos: {args.target_count}")
    print("=" * 80)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(args.checkpoint_file) or ".", exist_ok=True)

    try:
        raw_data = load_dolly_dataset(args.dataset, args.categories)
    except Exception as exc:
        print(f"❌ Erro ao carregar dataset: {exc}")
        return

    if not raw_data:
        print("❌ Nenhum registro disponível após filtros.")
        return

    random.shuffle(raw_data)
    sampling_queue = raw_data[: max(args.target_count * 2, args.target_count)]

    processed_indices = set()
    all_generated = []

    if os.path.exists(args.checkpoint_file):
        print(f"\n🔄 Checkpoint encontrado: '{args.checkpoint_file}'")
        with open(args.checkpoint_file, "r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                item = json.loads(line)
                processed_indices.add(item["source_idx"])
                all_generated.append(item["alpaca_item"])
        print(f"✅ Retomando com {len(all_generated)} exemplos de {len(processed_indices)} fontes.")

    total_generated = len(all_generated)
    if total_generated >= args.target_count:
        print(f"\n🎉 Meta de {args.target_count} exemplos já atingida!")
    else:
        print(f"\n🚀 Gerando exemplos CoT. Restante: {args.target_count - total_generated}...")

        for source_idx, sample in enumerate(sampling_queue):
            if total_generated >= args.target_count:
                break
            if source_idx in processed_indices:
                continue

            print(
                f"\n[{source_idx + 1}/{len(sampling_queue)}] "
                f"Categoria: {sample['category']} | "
                f"Pergunta: {sample['instruction'][:80]}..."
            )

            system_prompt, user_prompt = build_teacher_prompts(sample)
            raw_response = call_ollama_teacher(
                args.api_url, model_name, system_prompt, user_prompt
            )

            if not raw_response:
                print("⚠️  Sem resposta do professor. Pulando...")
                time.sleep(2)
                continue

            parsed = parse_llm_json(raw_response)
            if not parsed or "reasoning" not in parsed or "answer" not in parsed:
                print("⚠️  JSON inválido ou campos ausentes. Pulando...")
                time.sleep(1)
                continue

            reasoning = str(parsed["reasoning"]).strip()
            answer = str(parsed["answer"]).strip()
            if not reasoning or not answer:
                print("⚠️  Raciocínio ou resposta vazios. Pulando...")
                continue

            alpaca_item = {
                "instruction": sample["instruction"],
                "input": sample["context"] or "",
                "output": format_cot_output(reasoning, answer),
                "category": sample["category"],
                "teacher": teacher_key,
                "source_response": sample["response"],
            }

            all_generated.append(alpaca_item)
            processed_indices.add(source_idx)
            total_generated = len(all_generated)

            checkpoint_row = {
                "source_idx": source_idx,
                "teacher": teacher_key,
                "alpaca_item": alpaca_item,
            }
            with open(args.checkpoint_file, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(checkpoint_row, ensure_ascii=False) + "\n")

            print(f"✅ Exemplo gerado. Total: {total_generated}/{args.target_count}")
            time.sleep(0.5)

    print(f"\n💾 Salvando {len(all_generated)} exemplos em '{args.output}'...")
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(all_generated, handle, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("✅ Geração do dataset CoT concluída!")
    print(f"📁 Arquivo: {os.path.abspath(args.output)}")
    print(f"📝 Total de exemplos: {len(all_generated)}")
    print("=" * 80)


if __name__ == "__main__":
    main()
