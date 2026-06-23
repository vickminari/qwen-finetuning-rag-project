# Relatório Geral de Desempenho e Comparativo de Treinamentos (Q1, Q2 & Q3)

Este relatório compila os resultados experimentais obtidos em todas as fases do projeto de adaptação e ajuste do modelo de linguagem **Qwen/Qwen3.5-2B-Base** para a disciplina de Tópicos em IA da UFPI/CCN/DC.

Abaixo estão apresentados e discutidos os resultados quantitativos e qualitativos obtidos nas seguintes etapas:
1. **Continual Pre-Training (CPT) - Q1**: Pré-treinamento continuado utilizando o corpus de diários oficiais dos municípios do Piauí (**DOMPI-2025** / `diariosPrefeituras`), focado em aprender o domínio jurídico-administrativo público. O benchmark consiste em 30 perguntas específicas sobre decretos, portarias, contratos e licitações municipais.
2. **Supervised Fine-Tuning (SFT) com LoRA Padrão - Q2**: Ajuste fino supervisionado de instruções utilizando o dataset **docentesDC** (1.000 pares de perguntas e respostas geradas sobre os materiais didáticos e tópicos de computação dos docentes do DC/UFPI) com LoRA de rank $r=16$.
3. **Supervised Fine-Tuning (SFT) com rsLoRA - Q3**: Ajuste fino supervisionado de instruções sobre o mesmo dataset **docentesDC** (1.000 pares de perguntas e respostas), utilizando Rank-Stabilized LoRA (rsLoRA) com rank $r=64$ para maior capacidade e estabilidade.

---

## 📈 Tabela Comparativa de Métricas Quantitativas

A tabela abaixo resume as métricas quantitativas obtidas para cada fase. 
* O **CPT (Q1)** foi avaliado sobre o split de teste de texto bruto do `DOMPI-2025` (~1M tokens).
* O **SFT (Q2 & Q3)** foi avaliado sobre o split de teste de 100 perguntas e respostas reservado do dataset de instrução `docentesDC` (10% dos 1.000 pares originais).

| Fase / Experimento | Dataset Base | Parâmetros de Adaptação | Métrica | Modelo Baseline (Base) | Modelo Adaptado | Mudança Absoluta | Tempo de Treino |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **Q1: Continual Pre-Training (CPT)** | `diariosPrefeituras` (DOMPI-2025) | LoRA completo / todas as camadas lineares ($r=256, \alpha=16$) | **Loss (Cross-Entropy)**<br>**Perplexidade (PPL)**<br>**Acurácia Top-1** | 1.7991<br>6.0443<br>61.39% | **0.9011**<br>**2.4624**<br>**78.59%** | -0.8980 (MELHOROU)<br>-3.5819 (MELHOROU)<br>+17.20% (MELHOROU) | ~25 min (WSL) |
| **Q2: SFT (Standard LoRA)** | `docentesDC` (1.000 pares) | LoRA de atenção e projeções ($r=64, \alpha=16$) | **Loss (Cross-Entropy)**<br>**Perplexidade (PPL)** | 1.9233<br>6.8436 | **1.2268**<br>**3.4101** | -0.6965 (MELHOROU)<br>-3.4335 (MELHOROU) | 13m04s (Active)<br>~15m29s (Total) |
| **Q3: SFT (Rank-Stabilized LoRA)** | `docentesDC` (1.000 pares) | rsLoRA de atenção e projeções ($r=64, \alpha=16$) | **Loss (Cross-Entropy)**<br>**Perplexidade (PPL)** | 1.9225<br>6.8381 | **1.4524**<br>**4.2734** | -0.4701 (MELHOROU)<br>-2.5647 (MELHOROU) | 12m03s (Active)<br>~14m18s (Total) |

> [!NOTE]
> As pequenas discrepâncias nos valores do *Modelo Baseline* de validação ocorrem devido a pequenas variações de precisão numérica (bfloat16 vs float16) durante a inferência paralela no hardware da GPU RTX 4070 (8GB).

---

## 🔬 Análise Técnica dos Resultados

### 1. Diferenças Técnicas Fundamentais: CPT (Q1) vs SFT (Q2 & Q3)

Embora ambas as etapas utilizem adaptadores PEFT/LoRA para treinar o modelo `Qwen/Qwen3.5-2B-Base` na GPU RTX 4070, elas possuem objetivos, estruturas de dados e configurações de rede fundamentalmente distintas:

- **Objetivo de Aprendizado e Otimização:**
  - **CPT (Questão 1):** O objetivo é a *adaptação de domínio*. O modelo aprende as nuances linguísticas, estruturas de frases, termos jurídicos e entidades de um domínio especializado (diários oficiais municipais).
  - **SFT (Questões 2 & 3):** O objetivo é o *alinhamento de comportamento*. O modelo é ensinado a seguir instruções do usuário, estruturando suas saídas de acordo com padrões de conversação humana.
- **Preparação e Mascaramento da Perda no Treinamento:**
  - **CPT (O que o define sob o capô):** O treinamento é executado como Causal Language Modeling puro. Utiliza-se agrupamento e empacotamento de textos (packing) em blocos de tamanho máximo (ex: 2048 tokens). A função de perda (Cross-Entropy) é calculada de forma global sobre **todos os tokens da sequência**. O modelo aprende a prever o próximo token em qualquer posição do texto corrido.
  - **SFT (O que o define sob o capô):** Utiliza-se um colador de dados especial (como o `DataCollatorForCompletionOnlyLM` do TRL) para mascarar os tokens correspondentes ao prompt do usuário. A função de perda (Cross-Entropy) é calculada e propagada **apenas nos tokens da resposta (output)**. O modelo não é penalizado nem treinado para aprender a prever o texto da instrução ou do contexto, mas tão somente para gerar a resposta ideal dado o prompt como gatilho.
- **Módulos e Camadas do Adaptador LoRA:**
  - **CPT:** Como a adaptação de domínio exige uma remodelagem sutil do vocabulário e da semântica intrínseca das palavras, as matrizes de projeção do adaptador LoRA são aplicadas a **todas as camadas lineares**, incluindo a camada de entrada de tokens (**`embed_tokens`**) e a cabeça de predição do modelo de linguagem (**`lm_head`**). O rank escolhido é muito elevado ($r=256$) para expandir ao máximo a capacidade do modelo de reter novas informações factuais estruturadas.
  - **SFT:** Como a tarefa de alinhamento consiste em aprender o estilo de resposta e rotear a atenção de forma adequada (e não em alterar o vocabulário base), as camadas `embed_tokens` e `lm_head` permanecem **congeladas**. O adaptador LoRA é aplicado apenas aos pesos de atenção e projeções MLP (`q_proj`, `v_proj`, `gate_proj`, `up_proj`, `down_proj`). O rank utilizado é menor ($r=64$) pois o foco principal é aprender a dinâmica das instruções, evitando o esquecimento catastrófico dos pesos originais.

---

### 2. Análise do CPT (Q1)
* **Dataset e Execução:** Focado no corpus bruto de diários oficiais dos municípios do Piauí (`diariosPrefeituras`). O modelo aprende a prever a próxima palavra com base no jargão jurídico-administrativo piauiense.
* **Métricas Obtidas:** O benchmark avalia a capacidade de autocompletar e recuperar fatos específicos de decretos e portarias, demonstrando uma melhora expressiva na acurácia top-1 (61.39% para 78.59%) e uma redução drástica da perplexidade de validação para **2.4624**.
* **Comparação Qualitativa (Modelo Baseline vs. Modelo CPT):**
  Uma análise minuciosa das respostas presentes em benchmark_comparison_report.md destaca as seguintes diferenças comportamentais:
  1. **Ancoragem ao Domínio Local vs. Alucinações Desconexas:**
     - O **Modelo Baseline** carece de informações sobre a localidade, gerando alucinações geograficamente incoerentes. Por exemplo, na Q27, ele indica o "Município de São José do Rio Preto", na Q25 cita a "Companhia de Energia Elétrica do Rio de Janeiro", e na Q28 alucina que a indenização foi gerada por "veículos Chevrolet Corsa".
     - O **Modelo CPT (rsLoRA)** apresenta alta relevância local. Mesmo quando alucina dados específicos, eles pertencem à realidade de Teresina, citando órgãos locais reais como **FMS** (Fundação Municipal de Saúde), **SEMEC**, **ETURB**, e **SEMA**, bem como endereços plausíveis do município (como na Q9: *"Rua Firmino Pires, nº 1175, bairro Centro... Teresina-PI"*).
  2. **Estruturação de Layouts de Diários Oficiais:**
     - O **Modelo CPT** internalizou a formatação tabular típica de publicações em diários oficiais, frequentemente gerando delimitadores e tabelas de dotação orçamentária (como `| ÓRGÃO | PROGRAMÁTICA | NATUREZA | VALOR` nas questões 5, 18 e 29) para organizar as informações financeiras.
     - O **Modelo Baseline** falha em manter a estrutura do texto corrido e, sendo um modelo de base sem fine-tuning de instrução, preenche lacunas com placeholders vazios (como na Q12: `1. A CONTRATANTE: Nome: Endereço: Telefone:`) ou cai em loops de preenchimento gerando perguntas e respostas fictícias adicionais.
  3. **Vocabulário de Negócio e Relações Semânticas:**
     - O **Modelo CPT** demonstra assimilação do jargão técnico municipal. Na Q19, ele associa a SDU Centro com "manutenção e iluminação pública" (em contraste com o baseline, que a associa a "serviços de saúde"); na Q15 menciona a "Unidade de Alimentação Escolar (UAE)", termo técnico real de merenda da SEMEC; e na Q23 conecta a Comercial Cirúrgica Rioclarense ao fornecimento de insumos hospitalares.
     - O **Modelo Baseline** restringe-se a respostas literais simples ou associa incorretamente siglas e nomes, como deduzir que a SMPM contratou a "SMPM Graphic" (Q9).
  4. **Instabilidade de Geração:**
     - Devido ao fato de ser um treinamento puramente de linguagem causal sem alinhamento de chat, ambos os modelos podem manifestar instabilidades na formatação e término do texto. Na Q25, por exemplo, o modelo CPT apresentou um loop de repetição infinita de caracteres (`C. A. L. C. C. C. C...`).
* **Arquivos de Resultados Relacionados:**
  - As métricas quantitativas de perplexidade e entropia estão registradas nos arquivos de resultados baseline_evaluation.json (antes do treino) e cpt_evaluation.json (pós-CPT).
  - A comparação lado a lado de inferências qualitativas no benchmark de 30 questões está salva no arquivo benchmark_comparison_report.md.

---

### 3. SFT: Standard LoRA (Q2) vs rsLoRA (Q3) — Comparação Controlada ($r=64$)
O experimento de pós-treino compara o LoRA padrão com o rsLoRA, ambos utilizando rank $r=64$ e $\alpha=16$ sobre 1.000 pares do dataset de instrução `docentesDC`.

* **O Papel do Escalonamento do rsLoRA:** 
  No LoRA clássico, a atualização dos pesos do adaptador é escalonada por $\frac{\alpha}{r}$. Para o rank $r=64$ com $\alpha=16$, o fator de escala é de $\frac{16}{64} = 0.25$.
  O rsLoRA (*Rank-Stabilized LoRA*) resolve a tendência de enfraquecimento das atualizações em ranks altos redefinindo o denominador para a raiz quadrada do rank, escalonando por $\frac{\alpha}{\sqrt{r}}$. No caso de $r=64$ com $\alpha=16$, o fator de escala do rsLoRA torna-se $\frac{16}{\sqrt{64}} = 2.0$. Isso fortalece o impacto das atualizações do adaptador no modelo.

* **Explicação Técnica da Diferença de Desempenho e Overfitting:**
  - O modelo **SFT Standard LoRA (Q2, r=64)** atingiu perplexidade de **3.4101** e perda de **1.2268** no teste.
  - O modelo **SFT rsLoRA (Q3, r=64)** obteve perplexidade de **4.2734** e perda de **1.4524** no teste.
  - **Análise:** O fator de escala 8 vezes maior do rsLoRA (2.0 vs 0.25 do LoRA padrão), associado à alta capacidade do rank $r=64$ em um dataset pequeno (1.000 pares), causou atualizações muito intensas que levaram o modelo rsLoRA a um sobreajuste (overfitting) acelerado nos padrões do conjunto de treino. Isso prejudicou sua capacidade de generalização no split de teste oculto. Em contrapartida, o LoRA padrão com fator de escala menor (0.25) atuou como uma regularização natural, adaptando-se de forma mais suave e generalizando melhor no teste.
  - **Tempo de Treinamento:** Ambos os modelos apresentaram tempo de treinamento ativo muito semelhante: **13m04s** (784 segundos) para o Standard LoRA de Q2 e **12m03s** (723.5 segundos) para o rsLoRA de Q3 na GPU RTX 4070 Laptop, confirmando que a introdução do cálculo de estabilização do rsLoRA não traz qualquer overhead computacional durante o fine-tuning.

* **Arquivos de Resultados Relacionados:**
  - Os resultados das métricas de avaliação quantitativas estão salvos em sft_evaluation.json (para Q2) e rslora_evaluation.json (para Q3).
  - Os relatórios lado a lado comparando as respostas geradas contra o modelo baseline para as 25 perguntas do benchmark estruturado de benchmark_sft.json estão salvos em sft_evaluation_report.md (para Q2) e rslora_evaluation_report.md (para Q3).

> [!TIP]
> **Conclusão Qualitativa:** No benchmark qualitativo de 25 perguntas (`benchmark_sft.json`), ambos os modelos pós-fine-tuning alcançaram alto grau de alinhamento e corretude nas respostas técnicas de computação e estrutura da UFPI. Entretanto, o modelo de Q2 (Standard LoRA) tendeu a apresentar respostas ligeiramente mais robustas e com menor repetição de padrões textuais decorados do treino. Para que o rsLoRA com rank 64 superasse o LoRA padrão neste cenário, seria necessário reduzir a taxa de aprendizado para compensar o forte escalonamento de escala 2.0, ou expandir o volume de dados do dataset.