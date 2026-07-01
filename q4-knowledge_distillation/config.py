"""
Configuração central da pipeline de Destilação de Conhecimento (Q4).

Altere TEACHER_KEY ou STUDENT_KEY nos scripts, ou passe --teacher / --student
via linha de comando, para trocar modelos sem editar o código dos scripts.
"""

import os

# =============================================================================
# Diretórios e caminhos padrão
# =============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

DATA_DIR = os.path.join(SCRIPT_DIR, "data")
COT_DATASET_PATH = os.path.join(DATA_DIR, "cot_dataset.json")
COT_CHECKPOINT_PATH = os.path.join(DATA_DIR, "cot_dataset_checkpoint.jsonl")
BENCHMARK_PATH = os.path.join(SCRIPT_DIR, "benchmark_kd.json")

REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
DEFAULT_OUTPUT_REPORT = os.path.join(REPORTS_DIR, "q4_kd_evaluation_report.md")
DEFAULT_OUTPUT_JSON = os.path.join(REPORTS_DIR, "q4_kd_evaluation.json")

DEFAULT_ADAPTER_DIR = os.path.join(SCRIPT_DIR, "models")

# =============================================================================
# Dataset fonte — presets com mapeamento de campos
# =============================================================================
DATASET_PRESETS = {
    "portuguese_dolly": {
        "hf_name": "botbotrobotics/PortugueseDolly",
        "split": "train",
        "instruction_field": "instruction",
        "context_field": "context",
        "context_fallbacks": ["input"],
        "response_field": "response",
        "response_fallbacks": ["output", "answer"],
        "category_field": "category",
        "description": "Dolly-15k traduzido para pt-BR (~15k exemplos)",
    },
    "canarim": {
        "hf_name": "dominguesm/Canarim-Instruct-PTBR-Dataset",
        "split": "train",
        "instruction_field": "instruction",
        "context_field": "context",
        "context_fallbacks": ["input"],
        "response_field": "output",
        "response_fallbacks": ["response", "answer"],
        "category_field": None,
        "description": "Instruções nativas em português (~316k exemplos)",
    },
}

DEFAULT_DATASET_PRESET = "portuguese_dolly"
DATASET_SEED = 42

# Atalhos derivados do preset padrão (retrocompatibilidade)
_DEFAULT_PRESET = DATASET_PRESETS[DEFAULT_DATASET_PRESET]
DATASET_HF_NAME = _DEFAULT_PRESET["hf_name"]
DATASET_SPLIT = _DEFAULT_PRESET["split"]
DOLLY_INSTRUCTION_FIELD = _DEFAULT_PRESET["instruction_field"]
DOLLY_CONTEXT_FIELD = _DEFAULT_PRESET["context_field"]
DOLLY_RESPONSE_FIELD = _DEFAULT_PRESET["response_field"]
DOLLY_CATEGORY_FIELD = _DEFAULT_PRESET["category_field"] or "category"

# =============================================================================
# Professores (Teachers) — servidos via Ollama
# =============================================================================
TEACHERS = {
    "qwen3-14b": {
        "ollama_name": "qwen3:14b",
        "display_name": "Qwen3-14B (Ollama)",
        "description": "Modelo professor grande — raciocínio CoT de alta qualidade",
    },
    "gemma3-12b": {
        "ollama_name": "gemma3:12b",
        "display_name": "Gemma3-12B (Ollama)",
        "description": "Modelo professor alternativo — diversidade de estilo de raciocínio",
    },
}

DEFAULT_TEACHER_KEY = "qwen3-14b"

# =============================================================================
# Alunos (Students) — treinados via Hugging Face + LoRA
# =============================================================================
STUDENTS = {
    "qwen2.5-7b": {
        "hf_name": "Qwen/Qwen2.5-7B-Instruct",
        "display_name": "Qwen2.5-7B-Instruct",
        "output_subdir": "qwen2.5-7b_sft",
        "lora_r": 16,
        "lora_alpha": 16,
    },
    "qwen3.5-2b": {
        "hf_name": "Qwen/Qwen3.5-2B-Base",
        "display_name": "Qwen3.5-2B-Base",
        "output_subdir": "qwen3.5-2b_sft",
        "lora_r": 16,
        "lora_alpha": 16,
    },
    "qwen2.5-1.5b": {
        "hf_name": "Qwen/Qwen2.5-1.5B-Instruct",
        "display_name": "Qwen2.5-1.5B-Instruct",
        "output_subdir": "qwen2.5-1.5b_sft",
        "lora_r": 8,
        "lora_alpha": 8,
    },
}

DEFAULT_STUDENT_KEY = "qwen3.5-2b"

# =============================================================================
# Ollama
# =============================================================================
OLLAMA_API_URL = "http://localhost:11434"
OLLAMA_TIMEOUT = 120
OLLAMA_TEMPERATURE = 0.1

# =============================================================================
# Geração do dataset CoT
# =============================================================================
COT_TARGET_COUNT = 1000
COT_BENCHMARK_SIZE = 100
BENCHMARK_SAMPLE_SIZE = 100

# =============================================================================
# Treinamento SFT (valores padrão — sobrescrevíveis via CLI)
# =============================================================================
SFT_EPOCHS = 3
SFT_BATCH_SIZE = 2
SFT_GRAD_ACCUM = 4
SFT_LEARNING_RATE = 2e-4
SFT_MAX_SEQ_LENGTH = 2048
SFT_TEST_SPLIT = 0.1

# =============================================================================
# Avaliação
# =============================================================================
EVAL_MAX_NEW_TOKENS = 512
EVAL_MAX_SAMPLES_PPL = 100
EVAL_SEED = 42

# =============================================================================
# Templates Alpaca (português do Brasil)
# =============================================================================
ALPACA_PROMPT = """Abaixo está uma instrução que descreve uma tarefa, combinada com uma entrada que fornece mais contexto. Escreva uma resposta que complete adequadamente o pedido.

### Instrução:
{}

### Entrada:
{}

### Resposta:
{}"""

ALPACA_PROMPT_EVAL = """Abaixo está uma instrução que descreve uma tarefa, combinada com uma entrada que fornece mais contexto. Escreva uma resposta que complete adequadamente o pedido.

### Instrução:
{}

### Entrada:
{}

### Resposta:
"""

ALPACA_PROMPT_TRAIN = ALPACA_PROMPT_EVAL + "{}"

# Marcadores internos para separar raciocínio e resposta no campo output
COT_REASONING_MARKER = "### Raciocínio:"
COT_ANSWER_MARKER = "### Resposta:"

# =============================================================================
# Helpers
# =============================================================================

def get_dataset_preset(preset_key=None):
    """Retorna configuração do preset de dataset (campos HF e mapeamento)."""
    key = preset_key or DEFAULT_DATASET_PRESET
    if key not in DATASET_PRESETS:
        raise ValueError(
            f"Preset '{key}' não encontrado. Opções: {list(DATASET_PRESETS.keys())}"
        )
    return key, DATASET_PRESETS[key]


def extract_dataset_field(row, primary, fallbacks=None):
    """Lê um campo do registro, tentando nomes alternativos se necessário."""
    candidates = [primary] if primary else []
    if fallbacks:
        candidates.extend(fallbacks)
    for name in candidates:
        if not name:
            continue
        value = row.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def normalize_source_row(row, preset):
    """Normaliza um registro bruto para instruction, context, response, category."""
    instruction = extract_dataset_field(
        row,
        preset["instruction_field"],
        ["prompt", "question"],
    )
    context = extract_dataset_field(
        row,
        preset.get("context_field"),
        preset.get("context_fallbacks", ["input"]),
    )
    response = extract_dataset_field(
        row,
        preset["response_field"],
        preset.get("response_fallbacks", ["output", "answer"]),
    )
    category_field = preset.get("category_field")
    category = extract_dataset_field(row, category_field) if category_field else ""
    if not category:
        category = "general"

    return {
        "instruction": instruction,
        "context": context,
        "response": response,
        "category": category,
    }


def get_teacher(teacher_key=None):
    key = teacher_key or DEFAULT_TEACHER_KEY
    if key not in TEACHERS:
        raise ValueError(f"Teacher '{key}' não encontrado. Opções: {list(TEACHERS.keys())}")
    return key, TEACHERS[key]


def get_student(student_key=None):
    key = student_key or DEFAULT_STUDENT_KEY
    if key not in STUDENTS:
        raise ValueError(f"Student '{key}' não encontrado. Opções: {list(STUDENTS.keys())}")
    return key, STUDENTS[key]


def get_adapter_path(student_key=None):
    _, student = get_student(student_key)
    return os.path.join(DEFAULT_ADAPTER_DIR, student["output_subdir"])


def format_cot_output(reasoning, answer):
    """Monta o campo output no formato Alpaca + CoT."""
    reasoning = (reasoning or "").strip()
    answer = (answer or "").strip()
    return f"{COT_REASONING_MARKER}\n{reasoning}\n\n{COT_ANSWER_MARKER}\n{answer}"


def parse_cot_output(text):
    """Extrai raciocínio e resposta de um texto no formato CoT."""
    if not text:
        return "", ""

    reasoning = ""
    answer = text.strip()

    if COT_REASONING_MARKER in text and COT_ANSWER_MARKER in text:
        after_reasoning = text.split(COT_REASONING_MARKER, 1)[1]
        parts = after_reasoning.split(COT_ANSWER_MARKER, 1)
        reasoning = parts[0].strip()
        answer = parts[1].strip() if len(parts) > 1 else ""
    elif COT_ANSWER_MARKER in text:
        answer = text.split(COT_ANSWER_MARKER, 1)[1].strip()

    return reasoning, answer


def alpaca_to_benchmark_item(instruction, input_val, output_val):
    """Converte um item Alpaca em formato de benchmark (prompt, reasoning, answer)."""
    reasoning, answer = parse_cot_output(output_val)
    return {
        "prompt": instruction,
        "input": input_val or "",
        "reasoning": reasoning,
        "answer": answer,
        "reference_output": output_val,
    }
