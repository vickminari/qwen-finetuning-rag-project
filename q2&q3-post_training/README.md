# Q2 - Geração de Perguntas e Respostas (Pós-Treino / SFT)

Este diretório contém o script para geração sintética de perguntas e respostas em português do Brasil a partir do dataset **DocentesDC**, a ser utilizado na etapa de Pós-Treinamento (Supervised Fine-Tuning - SFT).

## 🚀 Como Executar o Script

O script `generate_questions.py` foi projetado para rodar em Python padrão e se comunica com o seu modelo LLM local que pode estar servido pelo **Ollama** ou **vLLM**.

### Pré-requisitos
Certifique-se de que os pacotes necessários estão instalados:
```bash
pip install requests datasets tqdm
```

*(Opcional: Caso queira ler arquivos Parquet locais diretamente em vez do Hugging Face, instale também `pandas` e `pyarrow`).*

### 1. Executando com Ollama (Padrão)
Se o seu Ollama está rodando localmente (normalmente na porta `11434`) com o modelo `qwen3.5:9b` (ou similar):
```bash
python generate_questions.py --backend ollama --model qwen3.5:9b --target_count 1000
```

Se o seu modelo tiver outro nome ou tag, use a flag `--model`:
```bash
python generate_questions.py --backend ollama --model qwen2.5:7b --target_count 1000
```

### 2. Executando com vLLM
Se você está servindo o modelo usando vLLM (normalmente na porta `8000` com endpoint compatível com OpenAI):
```bash
python generate_questions.py --backend vllm --api_url http://localhost:8000 --model Qwen/Qwen3.5-2B-Instruct --target_count 1000
```

---

## ⚙️ Parâmetros Disponíveis

O script aceita as seguintes flags para customização:

| Parâmetro | Tipo | Padrão | Descrição |
| :--- | :---: | :---: | :--- |
| `--dataset` | str | `vickminari/docentesDC` | Nome do repositório no HF ou caminho de arquivo local (.jsonl ou .parquet) |
| `--backend` | str | `ollama` | Backend do LLM local (`ollama`, `vllm`, `openai`) |
| `--api_url` | str | *auto* | URL do servidor (padrão: `http://localhost:11434` para Ollama e `http://localhost:8000` para vLLM) |
| `--model` | str | `qwen3.5:9b` | Nome exato do modelo carregado no seu servidor local |
| `--target_count` | int | `1000` | Quantidade total de perguntas a serem geradas |
| `--questions_per_chunk` | int | `4` | Quantidade de perguntas solicitadas por requisição ao LLM |
| `--output` | str | `perguntas_docentes.json` | Nome do arquivo JSON final compilado |
| `--checkpoint_file` | str | `perguntas_docentes_checkpoint.jsonl` | Arquivo incremental para salvar progresso |
| `--chunk_size` | int | `2500` | Tamanho máximo em caracteres de cada bloco de texto enviado |
| `--seed` | int | `42` | Semente aleatória para consistência de amostragem |

---

## 🔄 Resiliência e Interrupções (Checkpointing)

Como a geração de 1.000 perguntas locais pode levar algum tempo, o script salva o progresso a cada chamada bem-sucedida da API local em um arquivo chamado `perguntas_docentes_checkpoint.jsonl`. 

* Se a geração for interrompida (queda de energia, encerramento do script, etc.), **basta rodar o mesmo comando novamente**.
* O script lerá o checkpoint, identificará quais chunks já foram processados e continuará exatamente do ponto onde parou.
* Ao atingir a meta (por exemplo, 1.000 perguntas), o arquivo final `perguntas_docentes.json` será automaticamente compilado com toda a lista de perguntas geradas no formato especificado.

---

## 👥 Curadoria Colaborativa com o Argilla

Para revisar e refinar o dataset em equipe, foram criados scripts de integração com o painel do **Argilla** hospedado no Hugging Face Spaces do seu grupo.

### 1. Enviar perguntas para o Argilla
Após a geração das perguntas, você pode enviá-las para a plataforma utilizando o script:
```bash
# Certifique-se de ter o pacote instalado: pip install argilla
python q2-post_training/push_to_argilla.py --file perguntas_docentes.json --dataset_name docentes_dc_sft
```
*(Se preferir enviar o progresso parcial do checkpoint sem esperar terminar as 1000, o script detectará automaticamente o arquivo `.jsonl` de checkpoint se o `.json` final não existir).*

### 2. Revisar na Interface Web
1. Acesse o painel do seu grupo em: https://vickminari-docentesdc-dataset-curation.hf.space
2. Os membros do grupo podem ler as instruções, aprovar ou rejeitar os pares, ou sugerir correções de texto nos campos opcionais de texto se houver erros de ortografia ou lógica.

### 3. Baixar o Dataset Revisado e Aprovado
Após a revisão humana, execute o script a seguir para baixar apenas as perguntas **aprovadas** e com todas as **correções de texto** já aplicadas:
```bash
python q2-post_training/pull_from_argilla.py --output perguntas_docentes_final.json --dataset_name docentes_dc_sft
```
O arquivo final `perguntas_docentes_final.json` conterá apenas os dados limpos e validados pelo grupo, pronto para o ajuste fino (SFT).

---

## 🏋️‍♂️ Executando o Pós-Treino (Supervised Fine-Tuning - SFT)

O script `sft_training.py` realiza o ajuste fino de instruções (SFT) do modelo base Qwen utilizando LoRA.

### Como rodar o Treinamento (Q2 - LoRA Padrão)
Para iniciar o fine-tuning usando os dados curados:
```bash
python q2-post_training/sft_training.py --model_name Qwen/Qwen3.5-2B-Base --dataset_path perguntas_docentes_final.json --output_dir ./q2_sft_model --epochs 3
```
*   *(Nota: Se você não realizou a etapa do Argilla ainda e deseja rodar o treino com o dataset bruto gerado inicialmente, altere `--dataset_path` para `perguntas_docentes.json`).*
*   *(Dica: Se a sua GPU estiver sem memória VRAM livre, adicione a flag `--load_in_4bit` para rodar o treino via QLoRA 4-bit).*

### Como rodar o Treinamento (Q3 - rsLoRA)
Para rodar a Questão 3 (rsLoRA), basta adicionar a flag `--use_rslora` e alterar a pasta de destino:
```bash
python q2-post_training/sft_training.py --model_name Qwen/Qwen3.5-2B-Base --dataset_path perguntas_docentes_final.json --output_dir ./q3_sft_model --epochs 3 --use_rslora
```

---

## 📊 Avaliação do Ajuste Fino (Baseline vs SFT)

O script `evaluate_sft.py` computa as métricas quantitativas (Perplexidade e Loss) e gera respostas qualitativas para um conjunto de perguntas do benchmark.

### Como rodar a Avaliação
Após concluir o treinamento SFT, execute:
```bash
python q2-post_training/evaluate_sft.py --model_name Qwen/Qwen3.5-2B-Base --adapter_path ./q2_sft_model --dataset_path perguntas_docentes_final.json
```
Este comando irá:
1. Carregar o modelo baseline e calcular a perplexidade no split de teste (10%).
2. Carregar o adaptador LoRA treinado e recalcular as métricas de validação.
3. Gerar um arquivo de benchmark com 25 questões (`benchmark_sft.json`).
4. Rodar a inferência das 25 questões no baseline e no modelo pós-SFT.
5. Salvar o relatório comparativo em [reports/q2_sft_evaluation_report.md](file:///c:/Users/jvict/victors/estudos/aulas/topc_ia/trabalho_final/qwen-finetuning-rag-project/reports/q2_sft_evaluation_report.md) e as métricas brutas em `reports/q2_sft_evaluation.json`.

*(Para avaliar o modelo da Questão 3, basta rodar o mesmo comando apontando `--adapter_path ./q3_sft_model`).*

