import os
os.environ["HF_TRUST_REMOTE_CODE"] = "1"
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from filters import input_guardrail, output_guardrail

def call_qwen_local(prompt: str) -> str:
    """Simulador (Mock) do Qwen otimizado usando dicionário de mapeamento."""
    prompt_lower = prompt.lower()
    
    # 1. Dicionário para respostas legítimas baseadas em palavras-chave
    respostas_validas = {
        "python": "O projeto utiliza Python 3.10.",
        "alucinações": "O RAG reduz alucinações fornecendo documentos reais.",
        "requirements.txt": "O requirements.txt serve para gerenciar as dependências.",
        "onde os guardrails atuam": "Eles atuam antes do input e após o output.",
        "temperatura": "A temperatura foi definida como 0.1 para priorizar respostas factuais.",
        "o que é implementado": "A pasta q6-guardrails implementa validação estruturada.",
        "sentence-transformers": "SentenceTransformers foi sugerida para calcular similaridade.",
        "diferença básica": "Finetuning ajusta pesos e RAG injeta conhecimento.",
        "pydantic": "O guardrails-ai se integra com a biblioteca Pydantic.",
        "checkpoint final": "O checkpoint final é salvo no diretório ./results.",
        "privacidade": "Modelos Open-Source como o Qwen2.5 garantem privacidade.",
        "reduzir custos": "A validação programática reduz custos ao evitar chamadas à LLM."
    }
    
    # 2. Dicionário para simular respostas fora do contexto (Casos de Alucinação)
    respostas_alucinadas = {
        "bolo de cenoura": "Para fazer bolo de cenoura você precisa de cenouras, ovos, farinha e açúcar.",
        "1994": "O Brasil ganhou a copa do mundo de futebol em 1994.",
        "dólar": "A cotação atual do dólar comercial é de 5 reais e 40 centavos.",
        "pneu": "Para trocar o pneu, use o macaco para erguer o carro e solte os parafusos.",
        "lua": "A distância média da Terra até a Lua é de aproximadamente 384.400 quilômetros.",
        "elefante": "Um elefante adulto consome cerca de 150 kg de alimento por dia.",
        "dor de cabeça": "Você pode curar a dor de cabeça descansando em um ambiente escuro.",
        "mongólia": "A capital da Mongólia é Ulaanbaatar."
    }

    # Busca nos fluxos válidos usando um loop FOR chave/valor
    for chave, resposta in respostas_validas.items():
        if chave in prompt_lower:
            return resposta

    # Busca nos fluxos que simulam alucinação usando outro loop FOR
    for chave, resposta in respostas_alucinadas.items():
        if chave in prompt_lower:
            return resposta

    # Caso padrão se nada for encontrado
    return "Não encontrei essa informação no contexto fornecido."

def inicializar_modelo_real(model_name: str = "Qwen/Qwen3.5-2B-Base", adapter_path: str = "vickminari/qwen3.5-2b-sft-baseline"):
    """
    Carrega o modelo base e aplica o adaptador LoRA de SFT do Hugging Face ou local.
    """
    print(f"[LLM] Carregando modelo base: {model_name}...")
    
    # Verifica se CUDA está disponível para melhor performance
    dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
    device_map = "auto" if torch.cuda.is_available() else {"": "cpu"}
    
    tokenizer_path = adapter_path if adapter_path else model_name
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        dtype=dtype,
        device_map=device_map,
        trust_remote_code=True
    )
    
    if adapter_path:
        from peft import PeftModel
        print(f"[LLM] Aplicando adaptador LoRA SFT de: {adapter_path}...")
        model = PeftModel.from_pretrained(model, adapter_path)
        
    model.eval()
    return model, tokenizer

def gerar_resposta_llm_real(prompt: str, model, tokenizer, max_new_tokens: int = 150) -> str:
    """
    Executa a geração de texto real no modelo carregado.
    """
    device = next(model.parameters()).device
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.1,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )
        
    input_length = inputs.input_ids.shape[1]
    generated_tokens = outputs[0][input_length:]
    return tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()

def gerar_resposta(
    pergunta: str,
    contexto: str,
    usar_guardrails: bool = True,
    usar_modelo_real: bool = False,
    model = None,
    tokenizer = None
) -> str:
    """
    Executa o fluxo de resposta, aplicando ou contornando os guardrails com base nas flags.
    """
    # ---- AVALIAÇÃO DO GUARDRAIL DE ENTRADA ----
    if usar_guardrails:
        if not input_guardrail(pergunta):
            return "⚠️ Erro de Segurança: Input do usuário detectado como potencialmente malicioso."

    # Constrói o Prompt estruturado
    prompt_instrucao = f"Contexto: {contexto}\n\nPergunta: {pergunta}"
    
    # Executa a inferência (Simulada ou Real)
    if usar_modelo_real and model is not None and tokenizer is not None:
        resposta_qwen = gerar_resposta_llm_real(prompt_instrucao, model, tokenizer)
    else:
        resposta_qwen = call_qwen_local(prompt_instrucao)

    # ---- AVALIAÇÃO DO GUARDRAIL DE SAÍDA (Evita Alucinação) ----
    if usar_guardrails:
        if not output_guardrail(resposta_qwen, contexto):
            return "⚠️ Bloqueio de Segurança: A resposta gerada divergiu do contexto permitido (Alucinação detectada)."

    return resposta_qwen

# Wrapper retrocompatível
def gerar_resposta_segura(pergunta: str, contexto: str) -> str:
    return gerar_resposta(pergunta, contexto, usar_guardrails=True, usar_modelo_real=False)

if __name__ == "__main__":
    ctx = "O repositório qwen-finetuning-rag-project aplica técnicas de RAG com segurança."
    qst = "O que o repositório faz?"
    
    resultado_validado = gerar_resposta_segura(qst, ctx)
    print("Resultado do Fluxo (Mock com Guardrails):", resultado_validado)