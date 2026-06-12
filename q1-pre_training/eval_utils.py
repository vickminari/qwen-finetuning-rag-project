import os
import json
import torch
import torch.nn as nn
from tqdm import tqdm
from datasets import load_dataset, concatenate_datasets, Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM

def load_and_prepare_dataset(
    tokenizer,
    dataset_name="gutoportelaa/DOMPI-2025",
    territories=None,
    split_ratio=0.1,
    max_seq_length=2048,
    seed=42,
    local_txt_path=None,
    only_eval=False,
    max_samples=None
):
    """
    Carrega o dataset e o prepara em blocos/chunks de max_seq_length tokens.
    Suporta carregamento direto do Hugging Face ou arquivo de texto local.
    """ 
    if hasattr(tokenizer, "tokenizer"):
        tokenizer = tokenizer.tokenizer
    all_splits = [
        "carnaubais", "tabuleiros_alto_parnaiba", "planice_litoran", "entre_rios",
        "vale_do_sambito", "vale_dos_rios_piaui_e_itaueiras", "cocais", "mangabeiras",
        "serra_da_capivara", "vale_do_rio_guaribas", "chapada_vale_do_rio_itaim", "vale_do_caninde"
    ]
    if territories is None:
        # Usamos carnaubais como padrão ou outro split pequeno disponível
        territories = ["carnaubais"]
    elif len(territories) == 1 and territories[0].lower() == "all":
        territories = all_splits

    raw_text = ""
    
    # Caso 1: Carregamento a partir de um arquivo de texto local
    if local_txt_path and os.path.exists(local_txt_path):
        print(f"📂 Carregando dados locais de: {local_txt_path}")
        with open(local_txt_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        dataset = Dataset.from_dict({"texto": [raw_text]})
    else:
        # Caso 2: Carregamento a partir do Hugging Face
        print(f"📥 Carregando dataset {dataset_name} do Hugging Face para os territórios: {territories}")
        try:
            ds_list = []
            for t in territories:
                print(f"  -> Baixando split/território: {t}")
                ds = load_dataset(dataset_name, name="raw", split=t)
                ds_list.append(ds)
            dataset = concatenate_datasets(ds_list)
        except Exception as e:
            print(f"❌ Erro ao carregar dataset do Hugging Face: {e}")
            print("💡 Dica: Verifique sua conexão com a internet ou se o nome do território está correto.")
            print("💡 Dica 2: Você pode passar o caminho de um arquivo local contendo textos usando o argumento '--local_txt'.")
            raise e

    dataset_to_process = dataset
    is_split_before = False
    
    if only_eval and not (local_txt_path and os.path.exists(local_txt_path)) and len(dataset) > 10:
        print(f"✂️  Modo de avaliação detectado. Otimizando carregamento...")
        # Divide o dataset bruto em treino/validação primeiro para evitar processamento inútil
        split_raw = dataset.train_test_split(test_size=split_ratio, seed=seed)
        raw_eval = split_raw["test"]
        
        # Limita o número de documentos brutos para economizar tempo de tokenização
        if max_samples is not None:
            # Pegamos uma quantidade generosa de documentos para garantir que teremos pelo menos max_samples chunks.
            # Geralmente cada documento tem bastante texto, então max_samples * 5 é extremamente seguro.
            generous_limit = min(len(raw_eval), max_samples * 5)
            raw_eval = raw_eval.select(range(generous_limit))
            print(f"⚡ Selecionados apenas os primeiros {generous_limit} documentos do split de teste para tokenização ultra-rápida.")
            
        dataset_to_process = raw_eval
        is_split_before = True

    print(f"⚙️  Tokenizando dataset (tamanho bruto: {len(dataset_to_process)} registros)...")
    
    # Tokeniza todo o texto
    def tokenize_function(examples):
        # O campo de texto do dataset DOMPI-2025 é 'texto'
        text_column = "texto" if "texto" in examples else (examples.column_names[0] if len(examples.column_names) > 0 else "")
        if not text_column:
            raise ValueError("Nenhuma coluna de texto encontrada no dataset.")
        
        # Junta todas as linhas de texto em cada batch com o token de fim de sequência do tokenizer
        concatenated_text = [t + tokenizer.eos_token for t in examples[text_column] if t]
        return tokenizer(concatenated_text, add_special_tokens=False)

    tokenized_dataset = dataset_to_process.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset_to_process.column_names,
        desc="Tokenizando textos"
    )

    # Concatena todos os IDs de token e agrupa em blocos de max_seq_length
    print(f"🧱 Agrupando tokens em chunks de seq_len = {max_seq_length}...")
    
    def group_texts(examples):
        # Concatena todos os inputs no batch
        concatenated_examples = {k: sum(examples[k], []) for k in examples.keys()}
        total_length = len(concatenated_examples[list(examples.keys())[0]])
        # Corta o excesso para caber em blocos exatos de max_seq_length
        total_length = (total_length // max_seq_length) * max_seq_length
        # Divide em chunks
        result = {
            k: [t[i : i + max_seq_length] for i in range(0, total_length, max_seq_length)]
            for k, t in concatenated_examples.items()
        }
        result["labels"] = result["input_ids"].copy()
        return result

    chunked_dataset = tokenized_dataset.map(
        group_texts,
        batched=True,
        desc=f"Agrupando em blocos de {max_seq_length}"
    )
    
    if is_split_before:
        print(f"✅ Dataset de validação preparado: {len(chunked_dataset)} chunks.")
        return {"test": chunked_dataset}
        
    # Divide em treino e validação (comportamento padrão)
    split_dataset = chunked_dataset.train_test_split(test_size=split_ratio, seed=seed)
    print(f"✅ Dataset preparado: {len(split_dataset['train'])} chunks de treino, {len(split_dataset['test'])} chunks de validação.")
    
    return split_dataset


def evaluate_model(model, tokenizer, eval_dataset, device, batch_size=1, max_samples=None):
    """
    Avalia o modelo nas métricas:
    - Cross-Entropy Loss
    - Perplexidade (PPL)
    - Acurácia de previsão de próximo token (top-1 e top-5)
    """
    if hasattr(tokenizer, "tokenizer"):
        tokenizer = tokenizer.tokenizer
    model.eval()
    total_loss = 0.0
    total_tokens = 0
    correct_top1 = 0
    correct_top5 = 0
    
    # Limita o número de amostras para avaliação se solicitado (útil para testes rápidos)
    eval_subset = eval_dataset
    if max_samples and max_samples < len(eval_dataset):
        eval_subset = eval_dataset.select(range(max_samples))
        
    print(f"🔍 Avaliando modelo em {len(eval_subset)} chunks...")
    
    loss_fn = nn.CrossEntropyLoss(reduction="sum")
    
    with torch.no_grad():
        for i in tqdm(range(0, len(eval_subset), batch_size), desc="Avaliando"):
            batch = eval_subset[i : i + batch_size]
            input_ids = torch.tensor(batch["input_ids"]).to(device)
            
            # Forward pass
            outputs = model(input_ids)
            logits = outputs.logits
            
            # Shift de tokens para Causal LM (next token prediction)
            # logits no instante t prevê token no instante t+1
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = input_ids[..., 1:].contiguous()
            
            # Flatten para Cross Entropy
            vocab_size = shift_logits.size(-1)
            flat_logits = shift_logits.view(-1, vocab_size)
            flat_labels = shift_labels.view(-1)
            
            # Ignora tokens de padding caso existam (labels == tokenizer.pad_token_id)
            # Mas como agrupamos por blocos exatos, geralmente todos são válidos
            mask = flat_labels != tokenizer.pad_token_id
            active_logits = flat_logits[mask]
            active_labels = flat_labels[mask]
            
            if len(active_labels) == 0:
                continue
                
            loss = loss_fn(active_logits, active_labels)
            total_loss += loss.item()
            total_tokens += len(active_labels)
            
            # Acurácia Top-1
            preds_top1 = active_logits.argmax(dim=-1)
            correct_top1 += (preds_top1 == active_labels).sum().item()
            
            # Acurácia Top-5
            _, preds_top5 = active_logits.topk(5, dim=-1)
            # Verifica se active_labels está presente em alguma das 5 posições de predição
            correct_top5 += (preds_top5 == active_labels.unsqueeze(-1)).any(dim=-1).sum().item()
            
    # Computa as médias globais
    mean_loss = total_loss / total_tokens if total_tokens > 0 else 0.0
    perplexity = torch.exp(torch.tensor(mean_loss)).item()
    acc_top1 = correct_top1 / total_tokens if total_tokens > 0 else 0.0
    acc_top5 = correct_top5 / total_tokens if total_tokens > 0 else 0.0
    
    metrics = {
        "cross_entropy_loss": mean_loss,
        "perplexity": perplexity,
        "top_1_accuracy": acc_top1,
        "top_5_accuracy": acc_top5,
        "evaluated_tokens": total_tokens
    }
    
    print("\n📈 Resultados da Avaliação:")
    print(f"  - Cross-Entropy Loss: {metrics['cross_entropy_loss']:.4f}")
    print(f"  - Perplexidade (PPL): {metrics['perplexity']:.4f}")
    print(f"  - Acurácia Top-1:     {metrics['top_1_accuracy']*100:.2f}%")
    print(f"  - Acurácia Top-5:     {metrics['top_5_accuracy']*100:.2f}%")
    
    return metrics


def run_qualitative_generation(model, tokenizer, prompts, device, max_new_tokens=100):
    """
    Gera texto para uma lista de prompts qualitativos e retorna os resultados.
    """
    if hasattr(tokenizer, "tokenizer"):
        tokenizer = tokenizer.tokenizer
    model.eval()
    results = {}
    print("\n✍️  Gerando saídas qualitativas...")
    
    for prompt in prompts:
        print(f"\n--- Prompt: '{prompt}' ---")
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id
            )
            
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(generated_text)
        results[prompt] = generated_text
        
    return results
