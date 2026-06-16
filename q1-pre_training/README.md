# Q1 — Pré-Treino Continuado (CPT) com rsLoRA e Unsloth

Este diretório contém os scripts necessários para implementar o **Pré-Treinamento Continuado (CPT)** de um modelo de linguagem (por padrão `Qwen/Qwen3.5-2B-Base`) adaptando-o ao domínio dos diários municipais do Piauí (`DOMPI-2025`), além dos scripts para avaliação do modelo antes (baseline) e depois (CPT) do ajuste.

---

## Estrutura de Arquivos

*   **`requirements.txt`**: Dependências de bibliotecas Python necessárias para rodar os códigos.
*   **`eval_utils.py`**: Módulo contendo funções utilitárias compartilhadas de tokenização, agrupamento de texto em chunks de tamanho fixo (`max_seq_length=2048`) e o loop de computação das métricas.
*   **`evaluate_baseline.py`**: Executa a avaliação do modelo base original (antes do treinamento) salvando as métricas de perda, perplexidade e acurácia de tokens.
*   **`cpt_training.py`**: Script de treinamento usando a biblioteca **Unsloth** com **rsLoRA** de rank `256` (contém fallback automático para Transformers/PEFT padrão se o Unsloth não estiver disponível).
*   **`evaluate_cpt.py`**: Carrega o modelo base original + os adaptadores LoRA treinados e executa o mesmo teste comparando as métricas obtidas contra o baseline.
*   **`evaluate_benchmark.py`**: Executa inferência comparativa em um conjunto de perguntas do usuário (benchmark de pelo menos 25 perguntas) e gera um relatório detalhado.

---

## Como Utilizar

### 1. Preparação do Ambiente

Antes de executar, instale as dependências:
```bash
pip install -r requirements.txt
```

> 💡 **Nota sobre o Unsloth:** O Unsloth acelera consideravelmente o treinamento e reduz o consumo de memória de vídeo. Recomenda-se instalá-lo de acordo com as instruções oficiais para Windows compatíveis com sua versão CUDA.

---

### 2. Passo 1: Avaliação do Modelo Baseline

Para mensurar o impacto do CPT, primeiro avaliamos o desempenho do modelo em sua versão original de fábrica nos diários municipais:

```bash
python evaluate_baseline.py --model_name "Qwen/Qwen3.5-2B-Base" --dataset_name "gutoportelaa/dom-pi-teresina-2025" --max_samples 50
```

*   `--model_name`: Identificador ou caminho local do modelo Hugging Face.
*   `--dataset_name`: *(Opcional)* O dataset do Hugging Face para carregar. Padrão: `"gutoportelaa/DOMPI-2025"`. Pode ser alterado para `"gutoportelaa/dom-pi-teresina-2025"` para uma amostra menor e de alta qualidade específica de Teresina.
*   `--territories`: Splits/territórios a serem baixados do dataset `gutoportelaa/DOMPI-2025` (ignorado se usar o dataset de Teresina).
*   `--local_txt`: *(Opcional)* Se você possuir os diários em texto unificados localmente, forneça o caminho do arquivo `.txt` (ex: `--local_txt "caminho/para/diarios.txt"`), evitando o download automático do Hugging Face.
*   `--max_samples`: Limita a quantidade de blocos (de 2048 tokens) para fins de velocidade na avaliação.

Isso salvará as métricas quantitativas e algumas gerações qualitativas no arquivo `reports/baseline_evaluation.json`.

---

### 3. Passo 2: Pré-Treinamento Continuado (CPT)

Execute o script de treinamento para ajustar o modelo nos diários oficiais. Ele já vem configurado com os parâmetros recomendados no planejamento (como `optim="adamw_8bit"`, `bf16=True`, `gradient_accumulation_steps=8` e `use_rslora=True`):

```bash
# Treino padrão com DOMPI-2025 usando territórios específicos
python cpt_training.py --model_name "Qwen/Qwen3.5-2B-Base" --territories "carnaubais" --epochs 1 --output_dir "./q1_cpt_model"

# OU treino com o dataset de Teresina (amostra menor, mais limpa e de melhor qualidade)
python cpt_training.py --model_name "Qwen/Qwen3.5-2B-Base" --dataset_name "gutoportelaa/dom-pi-teresina-2025" --epochs 1 --output_dir "./q1_cpt_model"
```

*   `--dataset_name`: O dataset do Hugging Face. Padrão: `"gutoportelaa/DOMPI-2025"`. Pode ser alterado para `"gutoportelaa/dom-pi-teresina-2025"`.
*   `--output_dir`: O local onde o modelo adaptado (pesos LoRA) e o tokenizer modificado serão salvos.
*   `--local_txt`: Permite treinar a partir de um arquivo `.txt` local.

Após a execução, os adaptadores finais estarão na pasta `./q1_cpt_model`.

---

### 4. Passo 3: Avaliação do Modelo Pós-Treino (CPT)

Com o modelo treinado (ou enquanto os checkpoints intermediários estão na pasta), avalie os resultados de perplexidade e perda no mesmo conjunto de validação:

```bash
python q1-pre_training/evaluate_cpt.py --model_name "Qwen/Qwen3.5-2B-Base" --adapter_path "./q1_cpt_model" --max_samples 50
```

> 💡 **Detecção Automática de Checkpoints:** Se o seu treinamento foi interrompido ou ainda está em andamento (ou seja, não foi salvo na raiz do diretório final), os scripts de avaliação detectam automaticamente a subpasta de checkpoint mais recente (ex: `checkpoint-1000`) dentro de `./q1_cpt_model` e carregam os adaptadores e o tokenizer a partir dela.

O script carregará o modelo base, aplicará o adaptador LoRA correspondente, computará as métricas e imprimirá uma tabela mostrando a evolução (ex: a queda na Perplexidade e no Cross-Entropy Loss). Os resultados são salvos em `reports/cpt_evaluation.json`.

---

### 5. Passo 4: Rodar o Benchmark de Perguntas e Respostas

Quando seu benchmark de pelo menos 25 perguntas e respostas de referência estiver estruturado em um arquivo JSON (ex: `benchmark_q1.json`), rode a comparação qualitativa lado a lado:

```bash
python evaluate_benchmark.py --benchmark_json "benchmark_q1.json" --adapter_path "./q1_cpt_model"
```

> 💡 *Caso você ainda não possua o arquivo `benchmark_q1.json` criado, a primeira execução deste script criará um arquivo de exemplo com essa extensão para demonstrar a estrutura aceita.*

Isso gerará o relatório Markdown `reports/benchmark_comparison_report.md` estruturando as perguntas, respostas de referência, respostas do modelo base e respostas do modelo CPT de forma comparativa.

---

## Métricas Avaliadas

*   **Cross-Entropy Loss (Entropia Cruzada):** A perda de predição do modelo (quanto menor, mais adaptado ao vocabulário administrativo-jurídico piauiense).
*   **Perplexidade (PPL):** Indica o quão "surpreso" o modelo fica ao ler as frases dos diários oficiais. Uma perplexidade menor indica maior compreensão do estilo linguístico do domínio.
*   **Acurácia de Token (Top-1 e Top-5):** Mede a taxa de acerto do modelo ao tentar prever o próximo token exato ou se o token correto está entre as 5 predições mais prováveis do modelo.
