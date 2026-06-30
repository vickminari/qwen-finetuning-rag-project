import os
os.environ["HF_TRUST_REMOTE_CODE"] = "1"
import sys
import json
import argparse
import torch
from datasets import Dataset

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from config import (
    ALPACA_PROMPT,
    COT_DATASET_PATH,
    SFT_EPOCHS,
    SFT_BATCH_SIZE,
    SFT_GRAD_ACCUM,
    SFT_LEARNING_RATE,
    SFT_MAX_SEQ_LENGTH,
    SFT_TEST_SPLIT,
    get_student,
    get_adapter_path,
)

try:
    from unsloth import FastLanguageModel
    UNSLOTH_AVAILABLE = True
except ImportError:
    UNSLOTH_AVAILABLE = False

from trl import SFTTrainer, SFTConfig

if not UNSLOTH_AVAILABLE:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig, get_peft_model, TaskType


def parse_args():
    parser = argparse.ArgumentParser(
        description="Treinamento SFT do aluno (Student) — Q4 Destilação de Conhecimento"
    )
    parser.add_argument(
        "--student",
        type=str,
        default=None,
        choices=["qwen2.5-7b", "qwen3.5-2b", "qwen2.5-1.5b"],
        help="Chave do aluno em config.STUDENTS",
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default=None,
        help="Sobrescreve o nome HuggingFace do modelo (opcional)",
    )
    parser.add_argument(
        "--dataset_path",
        type=str,
        default=COT_DATASET_PATH,
        help="Caminho do JSON Alpaca + CoT gerado pelos professores",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="Diretório de saída do adaptador LoRA (padrão: models/<student>_sft)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=SFT_EPOCHS,
        help="Número de épocas de treinamento",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=SFT_BATCH_SIZE,
        help="Batch size por dispositivo",
    )
    parser.add_argument(
        "--grad_accum",
        type=int,
        default=SFT_GRAD_ACCUM,
        help="Passos de acúmulo de gradiente",
    )
    parser.add_argument(
        "--learning_rate",
        type=float,
        default=SFT_LEARNING_RATE,
        help="Taxa de aprendizado",
    )
    parser.add_argument(
        "--max_steps",
        type=int,
        default=-1,
        help="Máximo de passos (-1 = usar épocas)",
    )
    parser.add_argument(
        "--max_seq_length",
        type=int,
        default=SFT_MAX_SEQ_LENGTH,
        help="Comprimento máximo de sequência",
    )
    parser.add_argument(
        "--lora_r",
        type=int,
        default=None,
        help="Rank LoRA (padrão: definido por student em config)",
    )
    parser.add_argument(
        "--lora_alpha",
        type=int,
        default=None,
        help="Alpha LoRA (padrão: definido por student em config)",
    )
    parser.add_argument(
        "--load_in_4bit",
        action="store_true",
        help="Ativa QLoRA 4-bit para economizar VRAM",
    )
    parser.add_argument(
        "--force_standard",
        action="store_true",
        help="Força Transformers + PEFT em vez de Unsloth",
    )
    parser.add_argument(
        "--no_resume",
        action="store_true",
        help="Desativa retomada automática de checkpoints",
    )
    return parser.parse_args()


def load_and_split_dataset(dataset_path):
    """
    Carrega o dataset CoT (formato Alpaca) e divide em treino/validação.
    Campos esperados: instruction, input, output.
    """
    paths_to_try = [dataset_path, COT_DATASET_PATH]
    data = None

    for path in paths_to_try:
        if os.path.exists(path):
            print(f"📂 Carregando dataset CoT de: {path}")
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            break

    if data is None:
        raise FileNotFoundError(
            f"Dataset CoT não encontrado. Caminhos tentados: {paths_to_try}"
        )

    alpaca_rows = []
    for row in data:
        if not isinstance(row, dict):
            continue
        instruction = row.get("instruction", "").strip()
        output = row.get("output", "").strip()
        if instruction and output:
            alpaca_rows.append({
                "instruction": instruction,
                "input": str(row.get("input", "") or "").strip(),
                "output": output,
            })

    print(f"✅ Carregados {len(alpaca_rows)} exemplos Alpaca + CoT.")
    dataset = Dataset.from_list(alpaca_rows)
    split = dataset.train_test_split(test_size=SFT_TEST_SPLIT, seed=42)
    return split["train"], split["test"]


def main():
    args = parse_args()
    _, student_cfg = get_student(args.student)

    model_name = args.model_name or student_cfg["hf_name"]
    output_dir = args.output_dir or get_adapter_path(args.student)
    lora_r = args.lora_r if args.lora_r is not None else student_cfg["lora_r"]
    lora_alpha = args.lora_alpha if args.lora_alpha is not None else student_cfg["lora_alpha"]

    print("=" * 80)
    print("🚀 SFT DO ALUNO (STUDENT) — Q4 DESTILAÇÃO DE CONHECIMENTO")
    print("=" * 80)
    print(f"Aluno: {student_cfg['display_name']}")
    print(f"Modelo HF: {model_name}")
    print(f"Dataset: {args.dataset_path}")
    print(f"Saída LoRA: {output_dir}")
    print(f"QLoRA 4-bit: {args.load_in_4bit}")
    print("=" * 80)

    use_unsloth = UNSLOTH_AVAILABLE and not args.force_standard
    if use_unsloth:
        print("⚡ Unsloth detectado — treinamento acelerado.")
    else:
        print("⚠️  Unsloth não detectado — usando Transformers + PEFT padrão.")

    dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16

    if use_unsloth:
        print(f"\n📥 Carregando {model_name} via Unsloth...")
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_name,
            max_seq_length=args.max_seq_length,
            dtype=dtype,
            load_in_4bit=args.load_in_4bit,
            trust_remote_code=True,
        )
        if hasattr(tokenizer, "tokenizer"):
            tokenizer = tokenizer.tokenizer

        print(f"🔧 Configurando LoRA (r={lora_r}, alpha={lora_alpha})...")
        model = FastLanguageModel.get_peft_model(
            model,
            r=lora_r,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            lora_alpha=lora_alpha,
            lora_dropout=0,
            bias="none",
            use_gradient_checkpointing="unsloth",
            random_state=3407,
            use_rslora=False,
        )
    else:
        print(f"\n📥 Carregando {model_name} via Transformers...")
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            dtype=dtype,
            device_map="auto",
            trust_remote_code=True,
        )
        model.gradient_checkpointing_enable()

        peft_config = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
        )
        model = get_peft_model(model, peft_config)

    model.print_trainable_parameters()

    try:
        train_dataset, eval_dataset = load_and_split_dataset(args.dataset_path)
    except Exception as exc:
        print(f"❌ Erro ao carregar dados: {exc}")
        return

    eos_token = tokenizer.eos_token if tokenizer.eos_token else "<|endoftext|>"

    def format_prompts(batch):
        texts = []
        for inst, inp, out in zip(batch["instruction"], batch["input"], batch["output"]):
            text = ALPACA_PROMPT.format(inst, inp if inp else "", out) + eos_token
            texts.append(text)
        return {"text": texts}

    print("\n✍️  Aplicando template Alpaca (instruction + input + output CoT)...")
    train_dataset = train_dataset.map(format_prompts, batched=True)
    eval_dataset = eval_dataset.map(format_prompts, batched=True)

    total_steps = (
        args.max_steps
        if args.max_steps > 0
        else (len(train_dataset) * args.epochs) // (args.batch_size * args.grad_accum)
    )
    warmup_steps = max(1, int(0.03 * total_steps))

    print("\n⚙️  Configurando argumentos de treinamento...")
    training_args = SFTConfig(
        output_dir=output_dir,
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        weight_decay=0.01,
        warmup_steps=warmup_steps,
        lr_scheduler_type="cosine",
        logging_steps=5,
        save_strategy="steps",
        save_steps=200,
        eval_strategy="steps",
        eval_steps=200,
        fp16=False,
        bf16=(dtype == torch.bfloat16),
        optim="adamw_8bit",
        seed=3407,
        remove_unused_columns=False,
        report_to="none",
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        dataset_num_proc=2,
        packing=False,
    )

    print("\n📦 Inicializando SFTTrainer...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        args=training_args,
    )

    resume_from_checkpoint = None
    if not args.no_resume and os.path.exists(output_dir):
        checkpoints = [
            os.path.join(output_dir, name)
            for name in os.listdir(output_dir)
            if name.startswith("checkpoint-") and os.path.isdir(os.path.join(output_dir, name))
        ]
        if checkpoints:
            checkpoints.sort(key=lambda path: int(path.split("-")[-1]))
            resume_from_checkpoint = checkpoints[-1]
            print(f"🔄 Retomando de: {resume_from_checkpoint}")

    print("\n🎬 Iniciando treinamento SFT do aluno...")
    trainer.train(resume_from_checkpoint=resume_from_checkpoint)

    print(f"\n💾 Salvando adaptador LoRA em: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    print("\n" + "=" * 80)
    print("✅ TREINAMENTO SFT DO ALUNO CONCLUÍDO!")
    print("=" * 80)


if __name__ == "__main__":
    main()
