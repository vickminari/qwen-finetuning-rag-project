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
# Dataset fonte (Databricks Dolly-15k)
# =============================================================================
DATASET_HF_NAME = "databricks/databricks-dolly-15k"
DATASET_SPLIT = "train"
DATASET_SEED = 42

# Campos esperados no Dolly-15k
DOLLY_INSTRUCTION_FIELD = "instruction"
DOLLY_CONTEXT_FIELD = "context"
DOLLY_RESPONSE_FIELD = "response"
DOLLY_CATEGORY_FIELD = "category"

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
