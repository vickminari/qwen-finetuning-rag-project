# Planejamento — Trabalho Final de Tópicos em IA (2026.1)
> **Disciplina:** Tópicos em IA · Prof. Raimundo Moura — UFPI/CCN/DC  
> **Ambiente:** Alienware i9 Ultra · 32GB RAM DDR5 · RTX 4070 8GB VRAM  
> **Modelo base escolhido:** `Qwen/Qwen3.5-2B-Base`

---

## Visão Geral das Etapas

| # | Tipo | Dataset | Modelo | Benchmark |
|---|------|---------|--------|-----------|
| Q1 | Pré-treino continuado (CPT) | [`DOMPI-2025`](https://huggingface.co/datasets/gutoportelaa/DOMPI-2025) | Qwen3.5-2B-Base | ≥25 Q&A |
| Q2 | Pós-treino SFT | `docentesDC` | Qwen3.5-2B-Base | — |
| Q3 | Pós-treino LoRA/QLoRA | `docentesDC` | Qwen3.5-2B-Base | — |
| Q4 | Destilação de conhecimento | Sintético | Teacher: 2B / Student: 0.8B | 100 Q&A |
| Q5 | RAG | [`DOMPI-2025`](https://huggingface.co/datasets/gutoportelaa/DOMPI-2025) ou `docentesDC` | Qwen3.5-2B (fine-tunado) | 30 Q&A |
| Q6 | Guardrails | — | Modelo de Q2 ou Q3 | 30 Q&A |

---

## Modelo Base

**Escolhido:** `Qwen/Qwen3.5-2B-Base`

- Pesos brutos disponíveis no Hugging Face, compatíveis com Transformers, vLLM e Unsloth
- Destinado a fine-tuning, CPT e pesquisa — **não** para uso direto em chat
- Cabe na RTX 4070 8GB com bf16 LoRA (~5GB VRAM de uso em treino)
- 32GB de RAM DDR5 permite CPU offloading de estados do otimizador

### Por que não o 4B?
O Qwen3.5-4B-Base exige ~10GB em bf16 LoRA — acima dos 8GB disponíveis. O 2B é o maior modelo treinável com segurança neste hardware.

### Por que não QLoRA (4-bit)?

QLoRA funciona quantizando os pesos do modelo para 4-bit antes do treino, reduzindo drasticamente o uso de VRAM. Na maioria dos modelos (Llama, Mistral, Qwen2.5), essa quantização introduz um erro pequeno e aceitável — o modelo aprende bem mesmo assim.

O problema com o Qwen3.5 é sua **arquitetura híbrida**: ele combina camadas de atenção convencionais com camadas chamadas *Gated Delta Networks*, um tipo de modelo de estado linear (SSM). Essas camadas têm distribuições de pesos muito diferentes das atenções tradicionais — algumas regiões têm valores muito mais sensíveis à precisão numérica. Quando você quantiza esses pesos para 4-bit, o erro de arredondamento nessas camadas é desproporcionalmente alto, o que degrada a qualidade do modelo de forma perceptível mesmo após o fine-tuning.

Em termos práticos: o modelo treinado com QLoRA vai gerar respostas piores do que um modelo treinado com bf16 LoRA, e essa diferença é grande o suficiente para a documentação oficial do Unsloth recomendar explicitamente **não usar QLoRA no Qwen3.5**, independentemente do tamanho (denso ou MoE).

Como o `Qwen3.5-2B-Base` em bf16 LoRA usa apenas ~5GB de VRAM — dentro dos 8GB disponíveis — não há motivo para sacrificar qualidade com QLoRA. O caminho correto é **bf16 LoRA**.

---

## Hardware e Limites Práticos

| Recurso | Disponível | Observação |
|---------|-----------|------------|
| VRAM | 8GB (RTX 4070) | Limite crítico — modelos até 2B em bf16 LoRA |
| RAM | 32GB DDR5 | Permite offloading de estados do otimizador |
| CPU | i9 Ultra | Auxilia pré-processamento e carregamento |
| Ambiente | Local (Windows/Linux) | Sem dependência de nuvem paga |

**Configuração Unsloth recomendada para todas as etapas de treino:**

```python
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name    = "Qwen/Qwen3.5-2B-Base",
    max_seq_length = 2048,      # nunca ultrapassar em 8GB de VRAM
    load_in_4bit  = False,      # QLoRA não recomendado no Qwen3.5
    load_in_16bit = True,       # bf16 LoRA — caminho correto
)

model = FastLanguageModel.get_peft_model(
    model,
    r              = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj"],
    lora_alpha     = 16,
    use_gradient_checkpointing = "unsloth",  # essencial em 8GB
    random_state   = 3407,
)
```

**Argumentos de treino para não estourar VRAM:**

```python
per_device_train_batch_size  = 1,
gradient_accumulation_steps  = 8,   # batch efetivo = 8 sem custo de VRAM
fp16                         = False,
bf16                         = True,
optim                        = "adamw_8bit",  # ~30% menos VRAM no otimizador
```

---

## Esclarecimento Conceitual: CPT, SFT e LoRA

Antes de detalhar cada etapa, é importante entender que **LoRA é um método de otimização**, enquanto **CPT e SFT são objetivos de treino**. São dimensões independentes:

| Dimensão | O que define |
|----------|-------------|
| **CPT / SFT** | *O que* o modelo aprende — o objetivo do treino |
| **LoRA / full FT** | *Como* os pesos são atualizados — o método de otimização |

Você pode combinar qualquer objetivo com qualquer método. No nosso caso, como temos 8GB de VRAM, usamos LoRA como método em todas as etapas — mas o objetivo muda:

**CPT (Continued Pretraining):** O modelo recebe texto bruto, sem rótulos. O objetivo de treino é o mesmo do pré-treino original: prever o próximo token. Não há pares instrução/resposta — apenas sequências de texto do domínio-alvo. O modelo aprende o vocabulário, estilo e conteúdo dos diários municipais. É "aprender a falar como os diários".

**SFT (Supervised Fine-Tuning):** O modelo recebe pares `instrução → resposta`. O objetivo é aprender a *seguir instruções* e responder perguntas de forma útil. Há rótulos explícitos — a resposta correta é fornecida durante o treino. É "aprender a responder perguntas sobre os docentes".

A diferença é o formato dos dados e o que o modelo está otimizando:

```
CPT  →  entrada: "O prefeito assinou o decreto nº 123..."   saída esperada: próximo token
SFT  →  entrada: "Quais os projetos do Prof. X?"             saída esperada: "O Prof. X desenvolve..."
```

**Por que Q2 e Q3 não são a mesma coisa, então?**

Ambas fazem SFT — o objetivo é igual. O que muda é o *método LoRA* usado:

- **Q2 — SFT com LoRA padrão:** usa o escalonamento clássico `alpha/rank`. Para ranks baixos (16, 32), funciona bem. É o baseline.
- **Q3 — SFT com rsLoRA:** usa `alpha/sqrt(rank)`. Para ranks maiores, esse escalonamento é matematicamente mais estável — evita que os gradientes explodam ou sumam. Também há menos "esquecimento catastrófico" do conhecimento pré-existente. O enunciado pede exatamente essa comparação: mesmo objetivo (SFT), métodos de atualização diferentes.

**Resumo visual:**

```
Q1: CPT + rsLoRA (rank 256)  →  adaptação de domínio, texto bruto
Q2: SFT + LoRA   (rank 16)   →  fine-tuning supervisionado, baseline
Q3: SFT + rsLoRA (rank 16)   →  fine-tuning supervisionado, método melhorado
```

---

## Q1 — Pré-treino Continuado (CPT)

**Objetivo:** Fazer o modelo aprender o domínio dos diários municipais (linguagem jurídico-administrativa brasileira) antes do fine-tuning supervisionado.

**Dataset:** [`gutoportelaa/DOMPI-2025`](https://huggingface.co/datasets/gutoportelaa/DOMPI-2025) — diários oficiais dos municípios do Piauí (Grupo 01)

**Ferramenta:** Unsloth CPT (`Trainer` com dados brutos de texto, sem pares instrução/resposta)

**Métricas de avaliação (antes e depois):**
- Perplexidade (`ppl`) no conjunto de validação
- Entropia cruzada (`cross-entropy loss`)
- Acurácia de previsão de tokens (top-1 e top-5)

**Benchmark:** Criar ao menos 25 pares de pergunta e resposta de referência sobre o conteúdo dos diários, no estilo explicado por Rogério Figueredo.

**Observações técnicas:**
- Para CPT, o Unsloth recomenda rsLoRA com rank 256, treinando todas as camadas lineares incluindo `embed_tokens` e `lm_head`
- Use `max_seq_length=2048` para caber na VRAM
- Avaliar o modelo *antes* do CPT (checkpoint base) e *depois* (checkpoint salvo)

```python
# Configuração específica para CPT (rank maior, todas as camadas)
model = FastLanguageModel.get_peft_model(
    model,
    r              = 256,     # rank maior para CPT
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj",
                      "embed_tokens", "lm_head"],  # essencial para CPT
    use_rslora     = True,    # rsLoRA para ranks maiores
    lora_alpha     = 16,
)
```

---

## Q2 — Pós-treino SFT com LoRA (Supervised Fine-Tuning)

**Objetivo:** Ensinar o modelo a *seguir instruções* e responder perguntas sobre os docentes do DC/UFPI. Diferente do CPT (que aprende a prever tokens em texto bruto), o SFT usa pares explícitos de instrução e resposta correta — o modelo é treinado a produzir exatamente aquela saída dada aquela entrada.

**Método:** LoRA padrão (rank 16, `alpha/rank`) — este é o **baseline** que Q3 irá comparar.

**Dataset:** `docentesDC` (arquivos `.txt` consolidados pelo Grupo 08)

**Formato dos pares (dicionário Python):**
```python
{
    "instruction": "Quais são as áreas de pesquisa do Prof. X?",
    "input": "",          # opcional — contexto adicional
    "output": "O Prof. X atua nas áreas de..."
}
```

**Requisito mínimo:** 1.000 pares de instrução/resposta (podem ser gerados sinteticamente com um LLM a partir dos `.txt`)

**Ferramenta:** Unsloth `SFTTrainer` (TRL)

**Avaliação:** Comparar métricas (perplexidade, BLEU, ROUGE-L) do modelo antes e depois do SFT.

---

## Q3 — Pós-treino SFT com rsLoRA

**Objetivo:** Repetir exatamente o mesmo experimento de Q2 (SFT sobre `docentesDC`), mas substituindo o método LoRA padrão pelo **rsLoRA** (*Rank-Stabilized LoRA*). O objetivo de treino é idêntico — o que muda é como os pesos são atualizados.

**O que é rsLoRA e por que é melhor?**

No LoRA padrão, a atualização de pesos é escalonada por `alpha/rank`. Quando você aumenta o rank (ex: de 16 para 64 ou 256), esse escalonamento faz os gradientes ficarem cada vez menores, o que dificulta o aprendizado. O rsLoRA corrige isso usando `alpha/sqrt(rank)` — matematicamente mais estável para ranks maiores, preserva a escala dos gradientes independentemente do rank escolhido. Na prática, isso significa:

- Menos esquecimento catastrófico do conhecimento pré-existente
- Aprendizado mais estável com ranks maiores
- Resultados superiores ao LoRA padrão especialmente em CPT (Q1 usa rsLoRA com rank 256 por esse motivo)

**O que comparar entre Q2 e Q3:**
- Qualidade das respostas no benchmark (perplexidade, BLEU, ROUGE-L)
- Estabilidade da curva de loss durante o treino
- Uso de VRAM e tempo de treino (devem ser similares)

**Dataset:** mesmo `docentesDC` de Q2 — os datasets devem ser idênticos para a comparação ser válida

---

## Q4 — Destilação de Conhecimento

**Objetivo:** Transferir o conhecimento do modelo fine-tunado (teacher) para um modelo menor (student).

**Adaptação para o hardware disponível:**
- **Teacher:** `Qwen3.5-2B` após fine-tuning de Q2/Q3 (~5GB VRAM)
- **Student:** `Qwen3.5-0.8B-Base` (~3GB VRAM)
- Ambos cabem na RTX 4070 com folga (rodando sequencialmente)

**Dataset:** Gerado sinteticamente — usar o próprio teacher para criar pares Q&A sobre os domínios dos datasets anteriores

**Processo:**
1. Gerar logits/soft labels do teacher para cada entrada do dataset
2. Treinar o student com combinação de `hard loss` (rótulo real) + `soft loss` (KL divergence com logits do teacher)
3. Avaliar teacher e student com benchmark de 100 perguntas

**Métricas:** Acurácia no benchmark, perplexidade, análise qualitativa de respostas

---

## Q5 — RAG (Retrieval-Augmented Generation)

**Objetivo:** Expandir a capacidade do modelo com recuperação de contexto externo, sem retreinar.

**Tipo de RAG a escolher (um dos três):**
- **Standard RAG** — recupera chunks relevantes e concatena ao prompt
- **Agentic RAG** — múltiplos agentes coordenam a recuperação
- **Self-Reflective RAG** — o modelo avalia e refina suas próprias respostas

**Stack recomendada:**
```
LangChain (pipeline RAG) + FAISS ou ChromaDB (vector store) + modelo local (vLLM ou llama.cpp)
```

**Dataset:** [`gutoportelaa/DOMPI-2025`](https://huggingface.co/datasets/gutoportelaa/DOMPI-2025) ou `docentesDC` (textos indexados como chunks no vector store)

**Benchmark:** 30 perguntas avaliadas com e sem RAG — medir ganho em precisão e relevância

---

## Q6 — Guardrails

**Objetivo:** Adicionar camadas de controle ao modelo para resolver o dilema Helpfulness vs Harmlessness.

**Modelo base:** Modelo fine-tunado de Q2 ou Q3

**Funcionalidades a implementar (ao menos algumas):**
- Bloqueio de tópicos proibidos
- Reescrita de prompts problemáticos
- Mascaramento de dados sensíveis (nomes, CPFs, endereços)
- Classificação de intenção do usuário

**Ferramentas:**
- `nemo-guardrails` (NVIDIA NeMo Guardrails)
- `guardrails-ai` (Guardrails AI)

**Benchmark:** 30 perguntas — metade benignas, metade adversariais — avaliar taxa de bloqueio correto vs bloqueio indevido (falsos positivos)

---

## Stack de Ferramentas Completa

| Ferramenta | Uso | Etapas |
|-----------|-----|--------|
| **Unsloth** | CPT, SFT, LoRA, rsLoRA — treino otimizado | Q1, Q2, Q3, Q4 |
| **Hugging Face Transformers** | Carregamento de pesos, tokenizer, avaliação | Todas |
| **TRL (SFTTrainer)** | Loop de fine-tuning supervisionado | Q2, Q3 |
| **PEFT** | Adaptadores LoRA/rsLoRA | Q2, Q3 |
| **PyTorch** | Métricas de perplexidade e entropia | Q1, Q2, Q3, Q4 |
| **LangChain** | Pipeline RAG | Q5 |
| **FAISS / ChromaDB** | Vector store para RAG | Q5 |
| **NeMo Guardrails / Guardrails AI** | Camada de proteção | Q6 |
| **llama.cpp / vLLM** | Inferência local eficiente | Q5, Q6 |

### Instalação básica

```bash
# Unsloth (Windows/Linux com CUDA)
pip install unsloth

# Demais dependências
pip install transformers trl peft datasets accelerate bitsandbytes
pip install langchain faiss-cpu chromadb
pip install nemoguardrails
```

---

## Ordem de Execução Recomendada

```
Q1 (CPT) → Q2 (SFT) → Q3 (LoRA) → Q4 (Destilação) → Q5 (RAG) → Q6 (Guardrails)
```

As etapas Q2 e Q3 podem ser paralelas (mesmo dataset, abordagens diferentes). Q4 depende do modelo treinado em Q2/Q3. Q5 e Q6 dependem do modelo final disponível, mas não bloqueiam entre si.

---

## Referências

- [Dataset DOMPI-2025 (diários municipais) — Hugging Face](https://huggingface.co/datasets/gutoportelaa/DOMPI-2025)
- [Qwen3.5-2B-Base — Hugging Face](https://huggingface.co/Qwen/Qwen3.5-2B-Base)
- [Unsloth — Guia de fine-tuning Qwen3.5](https://unsloth.ai/docs/models/qwen3.5/fine-tune)
- [Unsloth — Continued Pretraining](https://unsloth.ai/docs/basics/continued-pretraining)
- [Unsloth — GitHub Releases](https://github.com/unslothai/unsloth/releases)
