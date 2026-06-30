import re

def input_guardrail(user_query: str) -> bool:
    """
    Retorna True se o input for seguro. Retorna False se detectar tentativa de burla.
    """
    # Lista de padrões regex comuns em ataques de Prompt Injection
    blacklist_patterns = [
        r"ignore\s+(as\s+)?(instruções|diretrizes|regras|restrições)",
        r"esqueça\s+(as\s+regras|as\s+diretrizes|as\s+instruções|o\s+filtro)",
        r"ignorando\s+(as\s+)?(regras|instruções|diretrizes|restrições)",
        r"act\s+as\s+a",
        r"agir\s+como\s+(um\s+)?(pirata|desenvolvedor|administrador|developer|modo)?",
        r"aja\s+como\s+(um\s+)?(pirata|desenvolvedor|administrador|developer|modo)?",
        r"você\s+agora\s+é\s+(um\s+)?(modo\s+)?developer",
        r"delete\s+system\s+prompt"
    ]
    
    query_lower = user_query.lower()
    for pattern in blacklist_patterns:
        if re.search(pattern, query_lower):
            return False
            
    # Bloqueia perguntas excessivamente longas que tentam estourar o contexto (exemplo)
    if len(user_query.split()) > 150:
        return False
        
    return True


def output_guardrail(resposta_gerada: str, contexto_recuperado: str) -> bool:
    """
    Verifica se a resposta do Qwen faz sentido com o contexto fornecido (Evita Alucinação).
    Uma abordagem simples é checar a intersecção de palavras-chave importantes.
    """
    # Limpa o texto básico para análise de palavras-chave
    def get_keywords(text):
        words = re.findall(r'\b\w{4,}\b', text.lower()) # palavras com mais de 4 letras
        # Remove stopwords comuns em português (simplificado)
        stopwords = {'para', 'com', 'uma', 'como', 'mais', 'pelo', 'pela', 'este', 'esta'}
        return set(words) - stopwords

    palavras_contexto = get_keywords(contexto_recuperado)
    palavras_resposta = get_keywords(resposta_gerada)
    
    # Se o modelo começar a falar sobre coisas que não têm NADA a ver com o contexto
    # (menos de 10% de correspondência de termos-chave), nós barramos.
    if not palavras_resposta: 
        return True # Resposta vazia ou curta demais para avaliar
        
    intersecricao = palavras_resposta.intersection(palavras_contexto)
    taxa_alinhamento = len(intersecricao) / len(palavras_resposta)
    
    # Se a taxa for muito baixa (ex: menor que 15%), o modelo pode estar alucinando fora do contexto
    if taxa_alinhamento < 0.15:
        return False
        
    return True