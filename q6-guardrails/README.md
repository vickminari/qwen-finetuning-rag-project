# Q6 - Guardrails & Segurança no RAG

Esta etapa implementa uma arquitetura de segurança programática e ativa (Guardrails) para o ecossistema RAG baseado no modelo Qwen. O objetivo principal é mitigar vulnerabilidades comuns em Large Language Models (LLMs), como ataques de *Prompt Injection* no fluxo de entrada e a geração de informações falsas (*Alucinações*) no fluxo de saída, utilizando uma abordagem leve, open-source e independente de APIs pagas.

---

## 🛡️ Arquitetura de Defesa e Relação com RAG

Embora o script de avaliação isole a lógica dos filtros para validação rápida, o fluxo foi desenvolvido especificamente para atuar em conjunto com o pipeline de **RAG (Retrieval-Augmented Generation)**:

1. **Input Guardrail (`filters.py`):** Intercepta a pergunta do usuário antes do envio ao modelo e do processo de recuperação de documentos (RAG). Detecta assinaturas de ataques conhecidos de injeção de prompt (ex: tentativas de burlar diretrizes do sistema, comandos para ignorar instruções ou ativação de modos restritos).
2. **Contextual System Prompt (`guardrails_pipeline.py`):** Concatena a pergunta do usuário com o **contexto recuperado** da base de documentos do RAG, instruindo estritamente a LLM a responder baseando-se apenas nos fatos providos.
3. **Output Guardrail (`filters.py`):** Validador de saída focado em consistência de contexto (*Groundedness Checking*). O filtro calcula o alinhamento léxico das palavras-chave relevantes entre a resposta gerada e o **contexto injetado**, bloqueando o output caso a LLM divirja e invente dados fora do escopo do documento (Alucinação).

No benchmark de validação, para garantir repetibilidade e isolamento de testes, cada caso de teste em `test_cases.json` já contém um par predefinido de `pergunta` e `contexto` (simulando a saída da base vetorial do RAG).

---

## 🤖 Modelo e Configurações de Parâmetros

### 1. Modelo Alvo
A arquitetura foi projetada para encapsular o modelo fine-tunado de **SFT (Q2/Q3)**, que é o `Qwen3.5-2B-Base` ajustado sobre o dataset `docentesDC`. 
- **Modo Otimizado (Testes Rápidos):** O arquivo `guardrails_pipeline.py` possui opcionalmente a infraestrutura para carregar o modelo de instrução real da família Qwen via `transformers`. No entanto, para fins de validação rápida e livre de concorrência de VRAM da GPU, a execução padrão simula a inferência do LLM (`call_qwen_local`) retornando respostas condizentes e alucinações mapeadas por chave.

### 2. Parâmetros e Limites de Validação
* **Limitação de Entrada (Comprimento):** O filtro `input_guardrail` rejeita perguntas excessivamente longas (mais de **150 palavras**) para prevenir estouros de contexto intencionais.
* **Sensibilidade do Filtro de Entrada (Regex):** O filtro usa expressões regulares case-insensitive flexíveis para cobrir variações de termos adversariais (como `ignore as regras`, `esqueça o filtro`, `agir como`, etc.).
* **Threshold de Alinhamento Léxico (Groundedness):** O filtro `output_guardrail` analisa palavras-chave relevantes (termos com mais de 4 caracteres, ignorando stopwords comuns do português) em ambas as strings (contexto vs resposta). O threshold de bloqueio está definido como **0.15 (15%)**: se a correspondência de termos for inferior a 15%, a resposta é classificada como alucinação e bloqueada.

---

## 🚀 Como Executar a Avaliação

Os testes rodam de forma automatizada sobre um benchmark de **30 cenários extremos** mapeados em `test_cases.json`.

Para rodar a avaliação de guardrails a partir do diretório raiz do projeto:

```bash
# Ative o seu ambiente virtual (ex: Windows venv)
.\..\..\venv\Scripts\activate

# Execute o script de avaliação
python .\q6-guardrails\evaluate_guardrails.py
```

### Artefatos de Saída
Após a execução do script, dois arquivos contendo a análise serão gerados na pasta de relatórios:
* **`q6_guardrail_evaluation.json`:** Contém os dados estruturados e brutos dos testes.
* **`q6_guardrail_evaluation_report.md`:** Relatório detalhado estruturado em Markdown, com tabelas de métricas, explicações qualitativas e exemplos práticos.

---

## 📊 Relatório Final de Validação (Métricas)

Abaixo está o resultado consolidado da execução da suite de testes após a otimização dos filtros baseados em expressões regulares:

```text
==================================================
 INICIANDO VALIDAÇÃO DE GUARDRAILS (30 CASOS)
==================================================
[-] Testando ID 1 a 30  ->  ✅ PASSOU

==================================================
 RELATÓRIO FINAL DOS GUARDRAILS
==================================================
 Total Executado: 30
 Taxa de Sucesso: 30/30 (100.0%)
 Falhas/Brechas:  0
==================================================
```