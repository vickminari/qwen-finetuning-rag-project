import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from filters import input_guardrail, output_guardrail

# 1. Configuração do modelo (Mantido opcional/mockado para os testes rápidos)
# Se você não quiser carregar o modelo real de 15GB durante os testes rápidos,
# deixe estas linhas de carregamento comentadas e use o simulador abaixo.
"""
model_name = "Qwen/Qwen2.5-7B-Instruct" 
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype="auto", device_map="auto")
"""
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

# 3. Execução do Fluxo Seguro (Nome ajustado para bater com o run_tests.py)
def gerar_resposta_segura(pergunta: str, contexto: str) -> str:
    # ---- AVALIAÇÃO DO GUARDRAIL DE ENTRADA ----
    if not input_guardrail(pergunta):
        return "⚠️ Erro de Segurança: Input do usuário detectado como potencialmente malicioso."

    # Constrói o Prompt estruturado
    prompt_instrucao = f"Contexto: {contexto}\n\nPergunta: {pergunta}"
    
    # Executa a inferência (Simulada pelo dicionário ou Real pelo Qwen)
    resposta_qwen = call_qwen_local(prompt_instrucao)

    # ---- AVALIAÇÃO DO GUARDRAIL DE SAÍDA (Evita Alucinação) ----
    if not output_guardrail(resposta_qwen, contexto):
        return "⚠️ Bloqueio de Segurança: A resposta gerada divergiu do contexto permitido (Alucinação detectada)."

    return resposta_qwen

# Exemplo de teste manual rápido
if __name__ == "__main__":
    ctx = "O repositório qwen-finetuning-rag-project aplica técnicas de RAG com segurança."
    qst = "O que o repositório faz?"
    
    resultado_validado = gerar_resposta_segura(qst, ctx)
    print("Resultado do Fluxo:", resultado_validado)