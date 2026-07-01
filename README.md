# Qwen Finetuning & RAG Project

Este repositório contém a infraestrutura e os códigos para a adaptação, alinhamento, otimização e controle de segurança da família de LLMs open-source **Qwen** (com foco no modelo `Qwen3.5-2B-Base`) para dois domínios de conhecimento especializados: o domínio jurídico-administrativo público municipal do Piauí e o domínio acadêmico-computacional do Departamento de Computação da UFPI.

---

## 🛠️ Visão Geral das Etapas

O projeto está dividido em seis questões integradas, cobrindo o ciclo completo de desenvolvimento de aplicações modernas de IA (desde o pré-treinamento até o alinhamento e monitoramento ativo):

### 1. Pré-Treino Continuado (CPT) — Q1
* **Objetivo:** Adaptar o modelo ao domínio jurídico-administrativo público municipal.
* **Dataset:** `diariosPrefeituras` (corpus `DOMPI-2025` unificado contendo publicações oficiais das prefeituras do Piauí).
* **Treinamento:** Continual Pre-Training (CPT) com Rank-Stabilized LoRA (rsLoRA, rank 256) em todas as camadas lineares (incluindo `embed_tokens` e `lm_head`) via Unsloth.
* **Avaliação:** Comparativo de Perplexidade (PPL), Cross-Entropy Loss e Acurácia de previsão de tokens sobre um benchmark de 30 perguntas específicas.
* **Detalhes:** Veja o diretório `q1-pre_training/`.

### 2. Pós-Treino SFT com LoRA — Q2
* **Objetivo:** Alinhamento comportamental do modelo para atuar como assistente acadêmico do DC/UFPI.
* **Dataset:** `docentesDC` (1.000 pares de perguntas e respostas gerados sinteticamente a partir de planos de curso e ementas).
* **Treinamento:** Supervised Fine-Tuning (SFT) com LoRA padrão (rank 64) via TRL (`SFTTrainer`).
* **Avaliação:** Perplexidade de validação e testes de seguimento de instruções (formato Alpaca).
* **Detalhes:** Veja o diretório `q2_q3-post_training/`.

### 3. SFT com rsLoRA (Estudo Comparativo) — Q3
* **Objetivo:** Avaliar o impacto do Rank-Stabilized LoRA (rsLoRA) em fine-tuning com datasets pequenos.
* **Treinamento:** Repetição exata do SFT do docentesDC substituindo o escalonamento clássico pelo rsLoRA (rank 64, $\alpha/\sqrt{r}$).
* **Avaliação:** Comparação direta de overfitting, tempo de treino, uso de VRAM e perplexidade side-by-side com o LoRA padrão de Q2.
* **Detalhes:** Veja o diretório `q2_q3-post_training/`.

### 4. Destilação de Conhecimento — Q4
* **Objetivo:** Transferir a capacidade cognitiva de um modelo maior (Teacher) para um modelo leve de baixo custo computacional (Student).
* **Configuração:** *Etapa em desenvolvimento.*
* **Status:** *Etapa em desenvolvimento.*

### 5. Retrieval-Augmented Generation (RAG) — Q5
* **Objetivo:** Enriquecer as respostas do modelo com recuperação semântica em tempo de execução sem alteração de pesos.
* **Tecnologia:** Pipeline de **Self-Reflective RAG** implementado como grafo de estados via **LangGraph**, usando banco vetorial **FAISS** e embeddings locais `BAAI/bge-m3`. A inferência e as auto-reflexões de groundedness e utilidade rodam no Ollama local (`qwen3.5:2b`).
* **Avaliação:** Cálculo automatizado das métricas RAGAS (Faithfulness, Answer Relevance, Context Precision, Context Recall) usando o `qwen3.5:9b` como juiz local sobre um benchmark de 30 perguntas.
* **Detalhes:** Veja o diretório `q5-rag_evaluation/`.

### 6. Guardrails (Segurança e Contenção) — Q6
* **Objetivo:** Blindagem ativa do sistema contra Prompt Injections no input e Alucinações no output.
* **Implementação:** Filtro de entrada (regex flexíveis case-insensitive) e filtro de saída (Groundedness Check léxico com threshold de 15% e stopwords customizadas).
* **Avaliação:** Benchmark de 30 cenários extremos avaliados com e sem a camada de guardrails sobre inferência real (carregando o modelo SFT de Q2 na GPU) e simulada, demonstrando o grau exato de contenção.
* **Detalhes:** Veja o diretório `q6-guardrails/`.

---

## 📂 Estrutura do Repositório

```text
├── q1-pre_training/           # Códigos, benchmark e instruções do CPT (Q1)
├── q2_q3-post_training/       # Códigos de treino e avaliação do SFT com LoRA/rsLoRA (Q2 & Q3)
├── q4-distillation/           # Código e avaliação da destilação do conhecimento do modelo (Q4)
├── q5-rag_evaluation/         # Agente LangGraph Self-Reflective RAG e RAGAS (Q5)
├── q6-guardrails/             # Pipeline e filtros de segurança programática (Q6)
├── reports/                   # Relatórios finais de avaliação (JSONs e Markdown)
└── requirements.txt           # Dependências unificadas do interpretador Python
```

*Nota: Os relatórios detalhados, tabelas lado a lado de inferências, gráficos de loss e perplexidades consolidados de cada etapa encontram-se centralizados na pasta `reports`.*

---

## 💻 Requisitos e Execução Geral

As dependências unificadas do projeto estão descritas no arquivo `requirements.txt`. O projeto foi desenvolvido e validado em ambiente local (Windows + WSL/Linux) com GPU compatível com CUDA.

### Configuração do Ambiente Virtual:
Para a execução das questões, recomenda-se a criação de um ambiente virtual Python (3.10 ou 3.12):

* **No Windows (venv local):**
  ```bash
  python -m venv venv
  .\venv\Scripts\activate
  pip install -r requirements.txt
  ```

* **No WSL/Linux (.venv para suporte CUDA/Triton):**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```

*Nota técnica: O carregamento de modelos reais da família Qwen3.5 contendo camadas Gated Delta Networks (SSM) exige suporte de compilação da biblioteca Triton, que não é compatível nativamente com Windows. Para execuções e treinos reais nestes modelos, utilize a venv do WSL/Linux.*

Para detalhes específicos sobre dados, parâmetros CLI e comandos de execução de cada fase, **consulte o README.md localizado na pasta correspondente**.

---

## 🎓 Informações do Projeto

Este repositório é a implementação prática do **Trabalho Final da disciplina de Tópicos em IA (Período 2026.1)**.
* **Instituição:** Universidade Federal do Piauí (UFPI) · Centro de Ciências da Natureza (CCN) · Departamento de Computação (DC)
* **Docente:** Prof. Raimundo Santos Moura
* **Ambiente de Validação:** Alienware i9 Ultra · 32GB RAM DDR5 · GPU Nvidia RTX 4070 (8GB VRAM)
