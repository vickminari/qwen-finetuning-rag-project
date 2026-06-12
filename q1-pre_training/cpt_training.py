import os
import argparse
import torch

# Tenta importar o Unsloth para aceleração (DEVE ser importado antes de transformers e peft)
try:
    from unsloth import FastLanguageModel
    UNSLOTH_AVAILABLE = True
except ImportError:
    UNSLOTH_AVAILABLE = False

from transformers import (
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    AutoModelForCausalLM,
    AutoTokenizer
)
from eval_utils import load_and_prepare_dataset

if not UNSLOTH_AVAILABLE:
    from peft import LoraConfig, get_peft_model, TaskType

def main():
    parser = argparse.ArgumentParser(description="Treinamento de Pré-treino Continuado (CPT) com rsLoRA")
    parser.add_argument(
        "--model_name",
        type=str,
        default="Qwen/Qwen3.5-2B-Base",
        help="Nome ou caminho do modelo base Hugging Face a ser treinado."
    )
    parser.add_argument(
        "--territories",
        type=str,
        nargs="+",
        default=["carnaubais"],
        help="Lista de territórios (splits) do dataset DOMPI-2025 para treinamento."
    )
    parser.add_argument(
        "--local_txt",
        type=str,
        default=None,
        help="Caminho opcional para arquivo de texto local com os diários."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./q1_cpt_model",
        help="Diretório onde os pesos ajustados (LoRA) e checkpoints serão salvos."
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=1,
        help="Número de épocas de treinamento."
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=1,
        help="Tamanho do lote por dispositivo de treino (per_device_train_batch_size)."
    )
    parser.add_argument(
        "--grad_accum",
        type=int,
        default=8,
        help="Passos de acúmulo de gradiente (gradient_accumulation_steps)."
    )
    parser.add_argument(
        "--learning_rate",
        type=float,
        default=2e-5,
        help="Taxa de aprendizado (learning_rate)."
    )
    parser.add_argument(
        "--max_steps",
        type=int,
        default=-1,
        help="Número máximo de passos de treino (-1 desativa e treina por épocas)."
    )
    parser.add_argument(
        "--eval_steps",
        type=int,
        default=500,
        help="Número de passos entre avaliações."
    )
    parser.add_argument(
        "--save_steps",
        type=int,
        default=500,
        help="Número de passos entre salvamentos."
    )
    parser.add_argument(
        "--max_eval_samples",
        type=int,
        default=500,
        help="Número máximo de chunks usados na avaliação durante o treino (0 = todos). "
             "Limitar a ~500 acelera muito a eval sem perder representatividade."
    )
    parser.add_argument(
        "--force_standard",
        action="store_true",
        help="Força o uso do Transformers + PEFT padrão ao invés do Unsloth."
    )
    parser.add_argument(
        "--lora_r",
        type=int,
        default=64,
        help="Rank do LoRA (r)."
    )
    parser.add_argument(
        "--lora_alpha",
        type=int,
        default=16,
        help="Alpha do LoRA (lora_alpha)."
    )
    parser.add_argument(
        "--no_resume",
        action="store_true",
        help="Desativa a retomada automática do treinamento a partir de checkpoints existentes."
    )
    parser.add_argument(
        "--train_embeddings",
        action="store_true",
        help="Treina também as camadas de embedding e lm_head (consome muito mais VRAM)."
    )
    parser.add_argument(
        "--max_seq_length",
        type=int,
        default=2048,
        help="Comprimento máximo de sequência (max_seq_length)."
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🚀 INICIANDO PRÉ-TREINAMENTO CONTINUADO (CPT) - Q1")
    print("=" * 80)
    print(f"Modelo Base: {args.model_name}")
    print(f"Diretório de saída: {args.output_dir}")
    
    use_unsloth = UNSLOTH_AVAILABLE and not args.force_standard
    if use_unsloth:
        print("⚡ Unsloth DETECTADO! O treinamento usará aceleração rápida e otimização de VRAM.")
    else:
        print("⚠️  Unsloth NÃO detectado ou desativado. Usando Transformers + PEFT padrão (mais lento/mais VRAM).")
        
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Configuração de Precisão de Tipo de Dados (bfloat16 se compatível)
    dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
    
    # ===== PASSO 1: Carregar Modelo e Tokenizer =====
    if use_unsloth:
        print(f"\n📥 Carregando {args.model_name} via Unsloth...")
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=args.model_name,
            max_seq_length=args.max_seq_length,
            dtype=dtype,
            load_in_4bit=False,  # CPT no Qwen3.5 não recomenda QLoRA 4-bit
            trust_remote_code=True,
        )
        if hasattr(tokenizer, "tokenizer"):
            tokenizer = tokenizer.tokenizer
        
        # Aplicar PEFT usando Unsloth
        print(f"🔧 Configurando rsLoRA de rank {args.lora_r} via Unsloth...")
        target_modules = [
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ]
        if args.train_embeddings:
            target_modules.extend(["embed_tokens", "lm_head"])
            
        model = FastLanguageModel.get_peft_model(
            model,
            r=args.lora_r,
            target_modules=target_modules,
            lora_alpha=args.lora_alpha,
            lora_dropout=0,
            bias="none",
            use_gradient_checkpointing="unsloth",  # Otimizado para 8GB
            random_state=3407,
            use_rslora=True,
        )
    else:
        print(f"\n📥 Carregando {args.model_name} via Transformers padrão...")
        tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            
        model = AutoModelForCausalLM.from_pretrained(
            args.model_name,
            dtype=dtype,
            device_map="auto",
            trust_remote_code=True
        )
        
        # Ativa gradient checkpointing para economizar VRAM
        model.gradient_checkpointing_enable()
        
        # Configurar rsLoRA padrão com PEFT
        print(f"🔧 Configurando rsLoRA de rank {args.lora_r} via PEFT padrão...")
        target_modules = [
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ]
        if args.train_embeddings:
            target_modules.extend(["embed_tokens", "lm_head"])
            
        peft_config = LoraConfig(
            r=args.lora_r,
            lora_alpha=args.lora_alpha,
            target_modules=target_modules,
            lora_dropout=0.05,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
            use_rslora=True
        )
        model = get_peft_model(model, peft_config)
        
    model.print_trainable_parameters()
    
    # ===== PASSO 2: Preparar Dataset =====
    print("\n📂 Carregando e preparando dados para o CPT...")
    try:
        dataset_split = load_and_prepare_dataset(
            tokenizer=tokenizer,
            territories=args.territories,
            local_txt_path=args.local_txt,
            split_ratio=0.1,
            max_seq_length=args.max_seq_length,
            seed=42
        )
        train_dataset = dataset_split["train"]
        eval_dataset = dataset_split["test"]
        
        # Limita o dataset de validação durante o treino para evitar eval lenta
        if args.max_eval_samples > 0 and len(eval_dataset) > args.max_eval_samples:
            print(f"✂️  Limitando eval de {len(eval_dataset)} → {args.max_eval_samples} chunks (treino mais rápido).")
            eval_dataset = eval_dataset.select(range(args.max_eval_samples))
    except Exception as e:
        print(f"❌ Erro na preparação dos dados: {e}")
        return
        
    # ===== PASSO 3: Configurar Argumentos de Treino =====
    print("\n⚙️  Configurando hiperparâmetros de treinamento...")
    
    # Calcula warmup_steps dinamicamente para evitar deprecation warning em transformers v5
    total_steps = args.max_steps if args.max_steps > 0 else (len(train_dataset) * args.epochs) // (args.batch_size * args.grad_accum)
    warmup_steps = max(1, int(0.03 * total_steps))
    
    training_args = TrainingArguments(
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
        save_steps=args.save_steps,
        eval_strategy="steps",
        eval_steps=args.eval_steps,
        fp16=False,
        bf16=(dtype == torch.bfloat16),
        optim="adamw_8bit",  # Economiza ~30% de VRAM do otimizador
        seed=3407,
        remove_unused_columns=False,
        report_to="none" # Evita tentar sincronizar com wandb ou outros
    )
    
    # ===== PASSO 4: Inicializar o Trainer =====
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )
    
    # ===== PASSO 5: Executar Treinamento =====
    print("\n🎬 Iniciando loop de treinamento...")
    
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
            print(f"🔄 Checkpoint detectado: {resume_from_checkpoint}. Retomando o treinamento...")
            
    trainer.train(resume_from_checkpoint=resume_from_checkpoint)
    
    # ===== PASSO 6: Salvar Pesos LoRA e Tokenizer =====
    print(f"\n💾 Salvando pesos do adaptador LoRA e Tokenizer em: {args.output_dir}")
    
    # Certifica-se de que a pasta existe
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Salva o adaptador
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    
    print("\n" + "=" * 80)
    print("✅ PRÉ-TREINAMENTO CONTINUADO (CPT) CONCLUÍDO COM SUCESSO!")
    print("=" * 80)
    print("Próximos passos:")
    print("1. Execute 'evaluate_cpt.py' para carregar e avaliar o modelo ajustado.")

if __name__ == "__main__":
    main()
