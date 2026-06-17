import os
os.environ["HF_TRUST_REMOTE_CODE"] = "1"
import json
import argparse
import torch
from datasets import Dataset

# Tenta importar o Unsloth para aceleração (deve ser importado antes de transformers e peft)
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
    parser = argparse.ArgumentParser(description="Treinamento Supervised Fine-Tuning (SFT) - Q2 & Q3")
    parser.add_argument(
        "--model_name",
        type=str,
        default="Qwen/Qwen3.5-2B-Base",
        help="Nome ou caminho do modelo base a ser treinado."
    )
    parser.add_argument(
        "--dataset_path",
        type=str,
        default="perguntas_docentes.json",
        help="Caminho do arquivo JSON contendo as perguntas/respostas para o SFT."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./q2_sft_model",
        help="Diretório onde os pesos LoRA e checkpoints serão salvos."
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Número de épocas de treinamento."
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=2,
        help="Tamanho do lote de treino por dispositivo (VRAM de 8GB: sugerido 2)."
    )
    parser.add_argument(
        "--grad_accum",
        type=int,
        default=4,
        help="Passos de acúmulo de gradiente (gradient_accumulation_steps)."
    )
    parser.add_argument(
        "--learning_rate",
        type=float,
        default=2e-4,
        help="Taxa de aprendizado para o otimizador."
    )
    parser.add_argument(
        "--max_steps",
        type=int,
        default=-1,
        help="Número máximo de passos (-1 desativa e treina por épocas)."
    )
    parser.add_argument(
        "--max_seq_length",
        type=int,
        default=2048,
        help="Comprimento máximo de sequência de tokens."
    )
    parser.add_argument(
        "--lora_r",
        type=int,
        default=16,
        help="Rank do LoRA (r). Q2: 16."
    )
    parser.add_argument(
        "--lora_alpha",
        type=int,
        default=16,
        help="Alpha do LoRA (lora_alpha). Q2: 16."
    )
    parser.add_argument(
        "--use_rslora",
        action="store_true",
        help="Ativa o Rank-Stabilized LoRA (rsLoRA). Necessário para a Questão 3."
    )
    parser.add_argument(
        "--load_in_4bit",
        action="store_true",
        help="Carrega o modelo base em QLora 4-bit para economizar ainda mais VRAM."
    )
    parser.add_argument(
        "--force_standard",
        action="store_true",
        help="Força o uso do Transformers + PEFT padrão ao invés do Unsloth."
    )
    parser.add_argument(
        "--no_resume",
        action="store_true",
        help="Desativa a retomada automática a partir de checkpoints existentes."
    )
    return parser.parse_args()

def load_and_split_dataset(dataset_path):
    """
    Carrega o dataset JSON de perguntas/respostas e realiza o split em treino (90%) e validação (10%).
    """
    # Tenta carregar o dataset final curado, senão tenta o gerado originalmente
    paths_to_try = [dataset_path, "perguntas_docentes_final.json", "perguntas_docentes.json"]
    data = None
    
    for path in paths_to_try:
        if os.path.exists(path):
            print(f"📂 Carregando dataset SFT de: {path}")
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            break
            
    if data is None:
        raise FileNotFoundError(
            f"Dataset de perguntas não encontrado nos caminhos tentados: {paths_to_try}."
        )
        
    print(f"✅ Carregados {len(data)} pares de perguntas e respostas.")
    
    # Criar Dataset do Hugging Face
    dataset = Dataset.from_list(data)
    
    # Split
    dataset_split = dataset.train_test_split(test_size=0.1, seed=42)
    return dataset_split["train"], dataset_split["test"]

# Template padrão Alpaca em português do Brasil
ALPACA_PROMPT = """Abaixo está uma instrução que descreve uma tarefa, combinada com uma entrada que fornece mais contexto. Escreva uma resposta que complete adequadamente o pedido.

### Instrução:
{}

### Entrada:
{}

### Resposta:
{}"""

def main():
    args = parse_args()
    
    print("=" * 80)
    print("🚀 INICIANDO SUPERVISED FINE-TUNING (SFT) - Q2 & Q3")
    print("=" * 80)
    print(f"Modelo Base: {args.model_name}")
    print(f"Dataset: {args.dataset_path}")
    print(f"rsLoRA Ativo: {args.use_rslora}")
    print(f"QLoRA 4-bit Ativo: {args.load_in_4bit}")
    print("=" * 80)

    use_unsloth = UNSLOTH_AVAILABLE and not args.force_standard
    if use_unsloth:
        print("⚡ Unsloth DETECTADO! O treinamento usará aceleração rápida e otimização de VRAM.")
    else:
        print("⚠️  Unsloth NÃO detectado ou desativado. Usando Transformers + PEFT padrão.")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16

    # ===== PASSO 1: Carregar Modelo e Tokenizer =====
    if use_unsloth:
        print(f"\n📥 Carregando {args.model_name} via Unsloth...")
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=args.model_name,
            max_seq_length=args.max_seq_length,
            dtype=dtype,
            load_in_4bit=args.load_in_4bit,
            trust_remote_code=True,
        )
        if hasattr(tokenizer, "tokenizer"):
            tokenizer = tokenizer.tokenizer

        # Configurar Adaptador LoRA/rsLoRA
        print(f"🔧 Configurando LoRA (r={args.lora_r}, alpha={args.lora_alpha}, rsLoRA={args.use_rslora}) via Unsloth...")
        model = FastLanguageModel.get_peft_model(
            model,
            r=args.lora_r,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            lora_alpha=args.lora_alpha,
            lora_dropout=0,
            bias="none",
            use_gradient_checkpointing="unsloth",  # Otimizado para economizar VRAM
            random_state=3407,
            use_rslora=args.use_rslora,
        )
    else:
        print(f"\n📥 Carregando {args.model_name} via Transformers...")
        tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            
        model = AutoModelForCausalLM.from_pretrained(
            args.model_name,
            dtype=dtype,
            device_map="auto",
            trust_remote_code=True
        )
        
        # Habilitar gradient checkpointing
        model.gradient_checkpointing_enable()
        
        # Configurar PEFT padrão
        print(f"🔧 Configurando LoRA (r={args.lora_r}, alpha={args.lora_alpha}, rsLoRA={args.use_rslora}) via PEFT...")
        peft_config = LoraConfig(
            r=args.lora_r,
            lora_alpha=args.lora_alpha,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
            use_rslora=args.use_rslora
        )
        model = get_peft_model(model, peft_config)

    model.print_trainable_parameters()
    
    # ===== PASSO 2: Carregar e Formatar os Dados =====
    try:
        train_dataset, eval_dataset = load_and_split_dataset(args.dataset_path)
    except Exception as e:
        print(f"❌ Erro ao carregar dados: {e}")
        return

    # Função de formatação do prompt (adiciona o token de fim para o modelo saber parar)
    EOS_TOKEN = tokenizer.eos_token if tokenizer.eos_token else "<|endoftext|>"
    
    def format_prompts(batch):
        instructions = batch["instruction"]
        inputs       = batch["input"]
        outputs      = batch["output"]
        texts = []
        for inst, inp, out in zip(instructions, inputs, outputs):
            # Formatar no template Alpaca e anexar o token de fim
            text = ALPACA_PROMPT.format(inst, inp if inp else "", out) + EOS_TOKEN
            texts.append(text)
        return { "text" : texts }

    print("\n✍️  Aplicando template Alpaca e formatando dados para o treino...")
    train_dataset = train_dataset.map(format_prompts, batched=True)
    eval_dataset = eval_dataset.map(format_prompts, batched=True)

    # ===== PASSO 3: Configurar Hiperparâmetros de Treinamento =====
    print("\n⚙️  Configurando argumentos de treinamento...")
    total_steps = args.max_steps if args.max_steps > 0 else (len(train_dataset) * args.epochs) // (args.batch_size * args.grad_accum)
    warmup_steps = max(1, int(0.03 * total_steps))

    training_args = SFTConfig(
        output_dir=args.output_dir,
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
        optim="adamw_8bit",  # Fundamental para GPU de 8GB
        seed=3407,
        remove_unused_columns=False,
        report_to="none",
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        dataset_num_proc=2,
        packing=False,
    )

    # ===== PASSO 4: Inicializar o SFTTrainer =====
    print("\n📦 Inicializando o SFTTrainer do TRL...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        args=training_args,
    )

    # ===== PASSO 5: Executar Treinamento =====
    print("\n🎬 Iniciando loop de treinamento SFT...")
    resume_from_checkpoint = None
    if not args.no_resume and os.path.exists(args.output_dir):
        checkpoints = [
            os.path.join(args.output_dir, d)
            for d in os.listdir(args.output_dir)
            if d.startswith("checkpoint-") and os.path.isdir(os.path.join(args.output_dir, d))
        ]
        if checkpoints:
            checkpoints.sort(key=lambda x: int(x.split("-")[-1]))
            resume_from_checkpoint = checkpoints[-1]
            print(f"🔄 Checkpoint detectado: {resume_from_checkpoint}. Retomando o SFT...")

    trainer.train(resume_from_checkpoint=resume_from_checkpoint)

    # ===== PASSO 6: Salvar Modelo e Tokenizer =====
    print(f"\n💾 Salvando pesos do adaptador LoRA e Tokenizer em: {args.output_dir}")
    os.makedirs(args.output_dir, exist_ok=True)
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    print("\n" + "=" * 80)
    print("✅ TREINAMENTO SUPERVISED FINE-TUNING (SFT) CONCLUÍDO COM SUCESSO!")
    print("=" * 80)

if __name__ == "__main__":
    main()
