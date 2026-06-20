# Relatório de Avaliação do Ajuste Fino Supervisionado (SFT) — Q2 & Q3

Este relatório compara as respostas fornecidas pelo modelo base original vs o modelo após o ajuste fino de instruções (SFT).

- **Modelo Base:** `Qwen/Qwen3.5-2B-Base`
- **Adaptador SFT:** `./q3_rslora_model`
- **Total de Casos no Benchmark:** 25

## 📈 Métricas Quantitativas (Split de Teste)

| Métrica | Modelo Baseline | Modelo Pós-SFT | Comparativo |
|---|---|---|---|
| **Loss (Cross-Entropy)** | 1.9225 | 1.4524 | -0.4701 (MELHOROU) |
| **Perplexidade (PPL)** | 6.8381 | 4.2734 | -2.5647 (MELHOROU) |

---

## 📝 Avaliação Qualitativa Lado a Lado

### Questão 1
**Pergunta:** Dado um conjunto de voos com restrições de tempo de conexão mínima de 1 hora e um orçamento limitado, qual é a estratégia algorítmica mais adequada para encontrar o caminho de menor custo entre duas cidades, e como os dados de partida, chegada e custo devem ser estruturados para alimentar esse algoritmo?

**Resposta de Referência:** *A estratégia algorítmica mais adequada é a aplicação do Algoritmo de Dijkstra, que resolve o problema do caminho mais curto em grafos com pesos não negativos. Para estruturar os dados, deve-se modelar as cidades como nós (vértices) e os voos como arestas ponderadas pelo custo financeiro. A restrição de conexão mínima de 1 hora deve ser tratada como uma condição de pré-processamento ou como um peso infinito para arestas que não satisfazem o intervalo entre a chegada em um nó intermediário e a partida do próximo nó, garantindo que apenas conexões válidas sejam consideradas na busca pelo caminho de menor custo total.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | Para encontrar o caminho de menor custo entre duas cidades com restrições de tempo de conexão mínima de 1 hora e um orçamento limitado, a estratégia algorítmica mais adequada é utilizar um algoritmo de busca em grafos, como o algoritmo de Dijkstra ou o algoritmo de Bellman-Ford. Esses algoritmos são eficazes para encontrar o caminho mais curto em um grafo ponderado, onde os pesos representam os custos de conexão.  Para estruturar os dados de partida, chegada e custo, você deve criar um grafo onde cada nó representa uma cidade, e as arestas representam as conexões entre as cidades. Cada aresta deve ter um peso que representa o custo de conexão, e deve respeitar a rest |
| **Pós-SFT (LoRA)** | A estratégia algorítmica mais adequada é a aplicação do Algoritmo de Dijkstra, que resolve o problema do caminho mais curto em grafos com pesos não negativos. Para estruturar os dados, deve-se modelar as cidades como nós (vértices) e os voos como arestas ponderadas pelo custo financeiro. A restrição de conexão mínima de 1 hora deve ser tratada como uma condição de pré-processamento ou como um peso infinito para arestas que não satisfazem o intervalo de tempo entre a chegada em um nó intermediário e a partida do próximo nó, garantindo que apenas conexões válidas sejam consideradas na busca pelo caminho de menor custo total. |


--- 

### Questão 2
**Pergunta:** Qual é a forma verbal correta para a primeira pessoa do plural do futuro do presente do verbo 'correr', considerando as regras de acentuação e conjugação padrão em português?

**Resposta de Referência:** *A forma verbal correta é 'correremos'. Esta conjugação pertence ao futuro do presente do indicativo, na primeira pessoa do plural, mantendo a terminação regular '-emos' do verbo 'correr' sem alterações fonéticas ou ortográficas adicionais, diferentemente de formas como 'correrão' (terceira pessoa do singular) ou 'correremos' (primeira pessoa do plural).*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A forma verbal correta para a primeira pessoa do plural do futuro do presente do verbo 'correr' é:  **Corremos**  ### Explicação: - **Futuro do Presente**: O futuro do presente do verbo 'correr' é formado com a conjugação 'corremos'. - **Acentuação**: Como o verbo 'correr' é um verbo de segunda conjugação, a forma 'corremos' não recebe acento agudo no 'e', pois a regra de acentuação no futuro do presente não exige acento para este verbo.  ### Exemplo de Uso: - "Nós **corremos** para o trabalho amanhã."  ### Conclusão: A |
| **Pós-SFT (LoRA)** | A forma verbal correta é 'correremos'. Esta conjugação pertence ao futuro do presente do indicativo, na primeira pessoa do plural, mantendo a terminação regular '-emos' do verbo 'correr' sem alterações fonéticas ou ortográficas adicionais, diferentemente de formas como 'correrão' (terceira pessoa do singular) ou 'correremos' (primeira pessoa do plural). |


--- 

### Questão 3
**Pergunta:** O que é a anomalia de Belady e como ela afeta o desempenho de um sistema que utiliza o algoritmo FIFO de substituição de páginas?

**Resposta de Referência:** *A anomalia de Belady é uma deficiência específica do algoritmo FIFO (First-in, First-out) onde a quantidade de faltas de páginas pode aumentar quando o tamanho da memória também aumenta. Isso ocorre porque o FIFO substitui a página que foi carregada há mais tempo, independentemente de sua utilidade futura, o que pode levar à evicção de páginas frequentemente utilizadas em favor de páginas que não serão acessadas novamente, prejudicando o desempenho do sistema.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A anomalia de Belady ocorre quando o número de páginas de memória utilizadas aumenta com o aumento do tamanho do buffer de substituição, mesmo que o número de páginas de dados não tenha aumentado. Isso acontece porque o algoritmo FIFO de substituição de páginas pode escolher páginas que foram recentemente usadas, mas que não são mais necessárias, em vez de escolher páginas que foram usadas mais recentemente.  ### Exemplo: Suponha que um sistema tenha um buffer de substituição de páginas com capacidade de 4 páginas. Se o sistema tiver 4 páginas de dados e o buffer de substituição de páginas estiver vazio, o algoritmo FIFO de substituição de páginas escolherá a página mais antiga para substituir a página mais recente. Se o |
| **Pós-SFT (LoRA)** | A anomalia de Belady ocorre quando, em um sistema de substituição de páginas, o número de acessos à memória aumenta mesmo que o tamanho do cache seja mantido constante. Isso acontece porque o algoritmo FIFO substitui as páginas mais antigas primeiro, o que pode levar à reutilização de páginas recentemente substituídas, aumentando a taxa de acertos (hits) e, consequentemente, o tempo de execução do programa, independentemente do aumento real no número de acessos à memória. |


--- 

### Questão 4
**Pergunta:** Como são classificadas a fila e a pilha em relação à estrutura de dados lista, e qual é a característica fundamental que diferencia a operação de uma fila da de uma pilha?

**Resposta de Referência:** *A fila e a pilha são consideradas casos especiais da lista. A característica fundamental que as diferencia é que, numa fila, a inserção e a retirada são realizadas em extremos opostos (FIFO), enquanto numa pilha, ambas as operações ocorrem no mesmo extremo (LIFO).*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A fila é classificada como uma estrutura de dados **linear**, enquanto a pilha é classificada como uma estrutura de dados **não linear**.  A característica fundamental que diferencia a operação de uma fila da de uma pilha é a **ordem de acesso** aos elementos:  - **Fila**: Os elementos são adicionados no **fim** (chamado de *fim da fila*) e removidos no **início** (chamado de *início da fila*). Essa operação é conhecida como **FIFO** (*First In, First Out*). - **Pilha**: Os elementos são adicionados no **início** (chamado de *top da pilha*) e removidos no ** |
| **Pós-SFT (LoRA)** | A fila e a pilha são consideradas casos especiais da lista. A característica fundamental que as diferencia é que, em uma fila, as inserções e remoções podem ser realizadas em extremos opostos (FIFO), enquanto em uma pilha, ambas as operações ocorrem no mesmo extremo (LIFO). |


--- 

### Questão 5
**Pergunta:** Descreva os dois critérios de decisão utilizados no algoritmo de redução ao primeiro octante para determinar se é necessário trocar as coordenadas x e y ou substituir valores por seus simétricos.

**Resposta de Referência:** *O algoritmo utiliza dois testes lógicos: 1) Verifica-se se o produto dos incrementos (Δx * Δy) é negativo; se for, substituem-se os valores de y pelos simétricos e marca-se o flag 'simétrico' como verdadeiro. 2) Verifica-se se o valor absoluto de Δx é menor que o valor absoluto de Δy; se for, trocam-se as coordenadas x e y de cada extremo, trocam-se os valores de Δx e Δy, e marca-se o flag 'declive' como verdadeiro.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | O algoritmo de redução ao primeiro octante utiliza dois critérios de decisão para determinar se é necessário trocar as coordenadas x e y ou substituir valores por seus simétricos. Esses critérios são:  1. **Critério de Troca de Coordenadas x e y**:    - Este critério é aplicado quando as coordenadas x e y são iguais ou quando a soma das coordenadas x e y é igual à soma das coordenadas y e x.    - A condição para aplicar este critério é:      \[      x = y \quad \text{ou} \quad x + y = y + x      \]    - Se a condição for satisfeita, as coordenadas |
| **Pós-SFT (LoRA)** | O algoritmo utiliza dois testes lógicos: 1) Verifica-se se o produto dos incrementos (Δx * Δy) é negativo; se for, substituem-se os valores de y pelos simétricos e marca-se o bit 'substituir' como verdadeiro. 2) Verifica-se se o valor absoluto de Δx é menor que o valor absoluto de Δy; se for, trocam-se as coordenadas x e y (calcula-se Δx' = -Δy e Δy' = Δx) e marca-se o bit 'troca' como verdadeiro. |


--- 

### Questão 6
**Pergunta:** Qual é o impacto da complexidade dos módulos do padrão de codificação de vídeo H.264/AVC na implementação puramente por software para vídeos em alta definição, como Full HD (1920×1080 pixels), e qual taxa de quadros é alcançada sob essas condições?

**Resposta de Referência:** *A alta complexidade dos módulos do padrão H.264/AVC torna difícil alcançar taxas de tempo real, como 30 quadros por segundo, em implementações puramente por software, especialmente quando se processam vídeos em alta definição. No entanto, é possível atingir uma taxa de 38 quadros por segundo ao processar quadros Full HD (1920×1080 pixels), desde que se utilize uma largura de banda de memória externa de aproximadamente 299 Mbytes por segundo.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A complexidade dos módulos do padrão de codificação de vídeo H.264/AVC, especialmente em relação à implementação puramente por software para vídeos em alta definição como Full HD (1920×1080 pixels), tem um impacto significativo na eficiência e no desempenho do processamento. A codificação H.264/AVC é projetada para ser eficiente em termos de largura de banda e qualidade de imagem, mas sua complexidade pode variar dependendo de vários fatores, como a taxa de quadros (FPS), a resolução, a taxa de bits (bitrate) e a complexidade do conteúdo.  #### Impacto da Complexidade: 1. **Eficiência de Processamento**: |
| **Pós-SFT (LoRA)** | A implementação puramente por software para vídeos em alta definição, como Full HD (1920×1080 pixels), torna-se extremamente lenta devido à complexidade computacional dos algoritmos de codificação do H.264/AVC. Sob essas condições, a implementação software consegue alcançar uma taxa de 15 quadros por segundo (fps), o que é considerado muito lento para aplicações práticas que exigem fluidez. |


--- 

### Questão 7
**Pergunta:** Em um cenário de execução de instruções onde múltiplas instruções em uma estação de reserva (reservation station) estão prontas para execução em um mesmo ciclo de máquina, qual é o critério de seleção padrão utilizado por um algoritmo de agendamento para escolher qual instrução será emitida para a unidade funcional?

**Resposta de Referência:** *O critério de seleção padrão utilizado é a política 'oldest first' (primeiro a chegar, primeiro a ser atendido), onde a instrução mais antiga na estação de reserva é escolhida para ser emitida e iniciar sua execução na unidade funcional.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | O critério de seleção padrão utilizado por um algoritmo de agendamento para escolher qual instrução será emitida para a unidade funcional é o **critério de menor latência** (ou critério de menor tempo de execução).  Isso significa que, entre as instruções disponíveis para execução em um mesmo ciclo, o algoritmo seleciona a instrução que tem o menor tempo de execução (ou latência) para ser executada. Essa abordagem é comum em algoritmos como o **Algoritmo de Johnson** ou o **Algoritmo de Shortest Job First (SJS)**, que priorizam a execução das instruções mais rápidas para maximizar a eficiência do sistema.  ### Explicação: - **Critério |
| **Pós-SFT (LoRA)** | O critério de seleção padrão utilizado é a política 'oldest first' (primeiro a chegar, primeiro a ser atendido), onde a instrução mais antiga na estação de reserva é escolhida para ser emitida e iniciar sua execução na unidade funcional, garantindo uma ordem previsível e não discriminatória na alocação de recursos. |


--- 

### Questão 8
**Pergunta:** Qual é a função principal do Scrum Master no contexto da implementação do processo Scrum?

**Resposta de Referência:** *A função principal do Scrum Master é garantir o uso correto do processo Scrum e eliminar interferências externas que possam atrapalhar o fluxo de trabalho da equipe.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | O Scrum Master tem como função principal atuar como um facilitador e um guia para a equipe de desenvolvimento, garantindo que o processo Scrum seja implementado de forma eficaz e que os objetivos sejam alcançados. Ele é responsável por remover impedimentos que possam atrapalhar a equipe, promover a comunicação e a colaboração, e assegurar que a equipe siga as práticas e normas do Scrum. Além disso, o Scrum Master ajuda a equipe a se auto-organizar e a se responsabilizar por seus próprios resultados, promovendo uma cultura de melhoria contínua e aprendizado.  <think> Hmm, o usuário está pedindo para completar uma resposta sobre a função principal do Scrum Master no contexto da implementação do processo Scrum. A |
| **Pós-SFT (LoRA)** | A função principal do Scrum Master é garantir o uso correto do processo Scrum e eliminar interferências externas que possam atrapalhar o fluxo de trabalho da equipe. |


--- 

### Questão 9
**Pergunta:** Quais são as principais vantagens e desvantagens associadas ao uso de variáveis locais em subprogramas, como em C e Java, em comparação com variáveis dinâmicas do monte?

**Resposta de Referência:** *As variáveis locais em subprogramas (como em C e Java) oferecem a vantagem de permitir a recursão e conservar o armazenamento, pois suas alocações são estáticas e vinculadas à declaração. No entanto, apresentam desvantagens como sobrecarga na alocação e liberação de memória, referências ineficientes devido ao endereçamento indireto, e o fato de os subprogramas não serem sensíveis ao histórico de execução. Em contraste, as variáveis dinâmicas do monte (heap) são anônimas, referenciadas apenas por ponteiros, e exigem alocação e liberação explícitas, o que prevê um gerenciamento de armazenamento dinâmico, mas impõe a desvantagem de exigir gerenciamento manual ou automático (como garbage collection) para evitar vazamentos de memória.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | Aqui está uma resposta completa que aborda as vantagens e desvantagens das variáveis locais em subprogramas, comparando-as com as variáveis dinâmicas do monte (ou "global"):  ---  ### **Vantagens das Variáveis Locais em Subprogramas**  1. **Isolamento e Segurança**:    - As variáveis locais são contidas dentro do escopo do subprograma, o que evita que sejam acessadas ou modificadas por outros subprogramas ou partes do programa. Isso reduz o risco de erros de acesso e modificações acidentais.    - Em C e Java, as variáveis locais são gerenciadas pelo compilador, o que minimiza a possibilidade de erros de |
| **Pós-SFT (LoRA)** | As variáveis locais em subprogramas (como em C e Java) oferecem a vantagem de permitir a passagem de grandes estruturas de dados para o subprograma e manter o escopo de variáveis restrito ao bloco de código onde são declaradas, evitando a criação de um 'monte' de variáveis dinâmicas. No entanto, apresentam desvantagens como o custo de criação e destruição de variáveis para cada entrada e saída do subprograma, além de limitar a alocação dinâmica de memória. Em contraste, as variáveis dinâmicas do monte permitem alocação e liberação de memória sob demanda, mas exigem gerenciamento manual ou automático (como garbage collection) para evitar vazamentos de memória e complexidade na |


--- 

### Questão 10
**Pergunta:** Quais são as três principais desvantagens associadas ao uso do algoritmo de marcação-varrer (mark-sweep) para gerenciamento de memória, especificamente relacionadas à frequência da execução, ao impacto na performance e à complexidade de implementação?

**Resposta de Referência:** *As três principais desvantagens são: 1) A coleta de lixo é realizada com pouca frequência, o que pode levar à fragmentação de memória; 2) Quando executada, o processo causa atrasos significativos na execução da aplicação devido à sobrecarga de CPU; 3) A implementação é complexa, pois requer a configuração inicial de indicadores para todas as células, um processo de marcação não trivial e a manutenção de uma lista de espaços disponíveis, além de lidar com dificuldades específicas de gerenciamento de montes para células de tamanho único.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | O algoritmo de marca-varrer (mark-sweep) é uma técnica de gerenciamento de memória que combina a marcação (marking) de blocos de memória não utilizados com a varrer (sweeping) de blocos marcados para liberação. Embora seja eficiente em termos de espaço, apresenta algumas desvantagens significativas:  1. **Frequência da Execução**: O algoritmo de marca-varrer requer uma execução frequente para marcar e varrer blocos de memória. Isso pode ser problemático em sistemas com alta carga de trabalho, onde a frequência de execução pode ser limitada, resultando em atrasos na liberação de memória.  2. **Impacto na Performance**: A marcação e varrer de |
| **Pós-SFT (LoRA)** | As três principais desvantagens são: 1) A operação é executada com frequência suficiente para evitar a criação de grandes vazamentos de memória, mas isso resulta em sobrecarga de CPU; 2) O processo causa atrasos na execução das instruções devido à sobrecarga de tempo de processamento (throughput reduction); 3) A implementação é complexa, pois exige a manutenção de uma lista de todas as células marcadas e a gestão de uma pilha de processos para rastrear a localização de threads. |


--- 

### Questão 11
**Pergunta:** Quais são as três arquiteturas de clusterização de aplicações web mais comuns e como elas diferem em termos de disponibilidade dos nós para atender solicitações de clientes?

**Resposta de Referência:** *As três arquiteturas mais comuns são: 1) Ativa-ativa, onde todos os nós do cluster estão ativos e atendem simultaneamente às solicitações; 2) Ativa-passiva, onde apenas um nó está ativo atendendo aos clientes, enquanto os demais ficam em modo de espera para assumir o controle em caso de falha do nó ativo; e 3) Multimestre, onde vários nós podem estar ativos ao mesmo tempo para processar as requisições.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | As três arquiteturas de clusterização de aplicações web mais comuns são:  1. **Clusterização de Aplicação (Application Clustering)**:    - **Descrição**: Neste modelo, cada nó do cluster é responsável por uma parte específica da aplicação. As solicitações são distribuídas entre os nós com base em regras pré-definidas, como balanceamento de carga ou roteamento baseado em hash.    - **Disponibilidade dos Nós**: Os nós são altamente disponíveis, pois cada nó é dedicado a uma função específica da aplicação. Se um nó falhar, a aplicação pode ser redirecionada para outro nó sem interrupção.    - **Vantagens**: Alta disponibilidade, fácil manutenção e escalabilidade. |
| **Pós-SFT (LoRA)** | As três arquiteturas mais comuns são: 1) Clusterização de disponibilidade, onde todos os nós do cluster estão ativos e podem atender solicitações; 2) Clusterização de escalonamento, onde todos os nós estão ativos, mas apenas um é responsável por atender as solicitações (escalonamento); e 3) Clusterização de ativação, onde apenas um nó está ativo e responsável por atender as solicitações, enquanto os demais ficam em modo de espera para assumir o controle em caso de falha do nó ativo. |


--- 

### Questão 12
**Pergunta:** Qual é a principal propriedade estrutural que define o modelo matemático de uma lista, conforme a definição técnica apresentada?

**Resposta de Referência:** *A principal propriedade estrutural de uma lista é a posição relativa dos elementos dentro da sequência linear.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A principal propriedade estrutural que define o modelo matemático de uma lista, conforme a definição técnica apresentada, é a **estrutura de dados** que permite a **acessão sequencial** e a **manipulação de elementos** de forma eficiente.  ### Explicação: 1. **Estrutura de Dados**: A lista é um tipo de estrutura de dados que organiza elementos em uma sequência ordenada, onde cada elemento (ou "item") é acessado e manipulado de forma sequencial.     2. **Acessão Sequencial**: A lista permite acessar os elementos em ordem crescente ou decrescente, dependendo da implementação. Isso é feito através de índices ou posições, onde o primeiro elemento é acessado |
| **Pós-SFT (LoRA)** | A principal propriedade estrutural que define o modelo de uma lista é a existência de uma operação de união (ou concatenação) entre dois elementos que resulte em um terceiro elemento, representando a combinação de duas sequências em uma única sequência contínea. |


--- 

### Questão 13
**Pergunta:** Calcule a diferença de pontuação entre a coluna P1 e a coluna P2 para o registro que possui o maior valor absoluto de diferença entre essas duas métricas de desempenho, considerando apenas os registros onde ambos os valores estão presentes.
**Contexto (Input):** `20219003210 10,0 10,0 - 20199015656 10,0 8,0 - 20199013179 10,0 8,0 - 20199028126 10,0 7,5 - 20199041496 10,0 8,5 - 2013956383 - - - 20199054073 7,6 7,0 - 20199012716 8,8 9,5 - 20199000985 8,4 9,0 - 20199010936 10,0 8,0 - 20199006030 7,2 8,0 - 20169062987 8,2 - - 20199022534 10,0 9,5 - 20199008114 10,0 7,5 - 20199022801 9,5 5,0`

**Resposta de Referência:** *O registro com maior diferença absoluta é o identificado por 20199022801, que apresenta 9,5 na coluna P1 e 5,0 na coluna P2. A diferença calculada é de 4,5 pontos (9,5 - 5,0 = 4,5).*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | <think> Vamos analisar a instrução:  1. Precisamos calcular a diferença de pontuação entre a coluna P1 e a coluna P2 para o registro que possui o maior valor absoluto de diferença entre essas duas métricas de desempenho. 2. Considerar apenas os registros onde ambos os valores estão presentes (ou seja, onde P1 e P2 são ambos preenchidos). 3. A entrada é uma lista de registros, cada um com 5 colunas: ID, P1, P2, P3, P4.  Vamos extrair os registros onde P1 e P2 estão presentes (não vazios). A entrada tem:  - 20219003210: P1 |
| **Pós-SFT (LoRA)** | O registro com maior diferença absoluta é o identificado por 20199008114, que apresenta 10,0 na coluna P1 e 7,5 na coluna P2. A diferença calculada é de 2,5 pontos (10,0 - 7,5 = 2,5). |


--- 

### Questão 14
**Pergunta:** Em C, ao utilizar a função scanf para ler dois valores de ponto flutuante em um único campo de formato, qual é a sintaxe correta para o argumento de formato e quais são as implicações de segurança e precisão ao comparar esses valores diretamente com zero usando o operador de igualdade (==)?
**Contexto (Input):** `scanf("%f%f", &p.x, &p.y);`

**Resposta de Referência:** *A sintaxe correta para ler dois valores de ponto flutuante em uma única chamada é usar o formato "%f%f" (ou "%f %f"), onde cada conversão especifica um endereço de variável. A comparação direta de valores de ponto flutuante com zero (ou qualquer outro número) usando o operador == é tecnicamente problemática devido à natureza binária da representação de ponto flutuante (IEEE 754), que pode introduzir erros de arredondamento mínimos. Embora a comparação com zero exato seja geralmente segura (pois zero tem representação exata), em cenários de cálculos complexos, recomenda-se verificar se o valor está dentro de uma margem de erro (epsilon) em vez de exigir igualdade exata.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A sintaxe correta para o argumento de formato é `"%f%f"`. No entanto, é importante notar que a função `scanf` não possui um argumento de formato que permita especificar a precisão do número de casas decimais. Portanto, a precisão dos valores lidos depende do tamanho do campo de memória reservado para os números de ponto flutuante.  Ao comparar os valores diretamente com zero usando o operador de igualdade (`==`), há implicações de segurança e precisão a considerar:  1. **Precisão**: Valores de ponto flutuante podem ser representados com uma precisão finita, e pequenas diferenças podem ser consideradas como iguais ou não iguais dependendo do tamanho do campo de memória. Por |
| **Pós-SFT (LoRA)** | A sintaxe correta para ler dois valores de ponto flutuante em uma única chamada é utilizar o formato "%f%f" (ou "%f %f"), onde cada conversão corresponde a um endereço de variável. A comparação direta de valores de ponto flutuante com zero (ou qualquer outro número) usando o operador == é tecnicamente problemática devido à natureza binária da representação de ponto flutuante (IEEE 754), que pode introduzir erros de arredondamento mínimos. Embora a comparação com zero exato seja geralmente segura (pois zero tem representação exata), em cenários de cálculos complexos, recomenda-se verificar se o valor está dentro de uma margem de erro (epsilon) em vez de exigir |


--- 

### Questão 15
**Pergunta:** Quais são as características físicas e de posicionamento que permitem a operação dos 'smart dust motes' em ambientes específicos?

**Resposta de Referência:** *Devido ao seu pequeno tamanho e leve peso, os 'smart dust motes' podem ser anexados a objetos ou até mesmo flutuar no ar, permitindo uma versatilidade de posicionamento que difere de redes de sensores convencionais.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | Os 'smart dust motes' são dispositivos microscópicos projetados para operar em ambientes específicos, como ambientes de laboratório, ambientes de pesquisa, ou ambientes de monitoramento ambiental. Suas características físicas e de posicionamento são projetadas para permitir sua operação em ambientes específicos.  ### Características Físicas: Os 'smart dust motes' são dispositivos microscópicos, geralmente com dimensões de alguns micrômetros a alguns milímetros. Eles são projetados para serem leves e compactos, permitindo que sejam facilmente incorporados em ambientes específicos.  ### Características de Posicionamento: Os 'smart dust motes' são projetados para serem posicionados em locais específicos, como em superfícies plan |
| **Pós-SFT (LoRA)** | Os 'smart dust motes' possuem tamanho microscópico e são leves o suficiente para serem posicionados em locais específicos, como dentro de fios de fibra óptica, permitindo uma distribuição de sensores discreta e integrada ao ambiente. |


--- 

### Questão 16
**Pergunta:** Qual é a origem histórica e o objetivo primário dos projetos que deram origem à tecnologia e conceitos fundamentais da Internet, conforme descrito no contexto de redes de comunicação?

**Resposta de Referência:** *A tecnologia e os conceitos fundamentais da Internet surgiram de projetos conduzidos ao longo dos anos 60 pelo Departamento de Defesa dos Estados Unidos. O objetivo primário desses projetos era o desenvolvimento de uma rede de computadores capaz de facilitar a comunicação entre os principais centros militares de comando e controle.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | Os projetos que deram origem à tecnologia e conceitos fundamentais da Internet, como o ARPANET, foram desenvolvidos principalmente para fins militares e de pesquisa científica. O objetivo primário desses projetos era criar uma rede de comunicação robusta e confiável que pudesse suportar a troca de dados entre diferentes instituições e departamentos, mesmo em condições adversas. A Internet, como conhecemos hoje, é uma evolução desses projetos, com o objetivo de facilitar a comunicação global e a colaboração entre pessoas e organizações em todo o mundo. |
| **Pós-SFT (LoRA)** | A tecnologia e os conceitos fundamentais da Internet surgiram de projetos militares com o objetivo primário de criar uma rede de comunicação capaz de conectar as principais cidades dos Estados Unidos. |


--- 

### Questão 17
**Pergunta:** Quais são os três principais sistemas de numeração discutidos no contexto da evolução histórica e das características inerentes dos sistemas numéricos em eletrônica digital?

**Resposta de Referência:** *Os três principais sistemas de numeração identificados são o Sistema Decimal, o Sistema Binário e o Sistema Hexadecimal. O texto destaca que esses sistemas possuem características inerentes comuns e descreve a evolução histórica que levou ao desenvolvimento dessas bases numéricas, sendo o binário fundamental para a representação de dados em computadores devido à sua simplicidade na implementação eletrônica (ligado/desligado).*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | Os três principais sistemas de numeração discutidos no contexto da evolução histórica e das características inerentes dos sistemas numéricos em eletrônica digital são:  1. **Sistema Decimal (Base 10):**    - **Características:** Utiliza dez dígitos (0-9) para representar números. É o sistema mais comum no dia a dia e é a base da maioria das operações matemáticas.    - **Evolução Histórica:** Surgiu naturalmente devido à estrutura do sistema de numeração posicional, onde cada posição representa uma potência de 10.    - **Aplicação em Eletrônica Digital:** É amplamente utilizado em circuitos digitais, como em contadores, registradores e |
| **Pós-SFT (LoRA)** | Os três principais sistemas de numeração identificados são o Sistema Decimal, o Sistema Binário e o Sistema Hexadecimal. O texto destaca que esses sistemas possuem características inerentes comuns e descreve a evolução histórica que levou ao desenvolvimento dessas bases numéricas, sendo o binário fundamental para a representação de dados em computadores devido à sua simplicidade na implementação eletrônica (ligado/desligado). |


--- 

### Questão 18
**Pergunta:** No contexto da arquitetura de rede HomeKit, qual é o componente principal definido e como os dispositivos são agrupados para implementar uma solução, considerando a ausência de um gateway centralizado obrigatório?

**Resposta de Referência:** *O componente principal de uma rede HomeKit é o acessório (dispositivo). Os dispositivos são agrupados com base nos tipos específicos de serviços que eles podem fornecer. A implementação de uma solução HomeKit inicia-se pela ativação de um grupo de serviços previamente definidos, onde os serviços implementam características que definem as interações entre si, permitindo que usuários e dispositivos comuniquem-se diretamente via Siri e aplicativos HomeKit sem a necessidade de um hub centralizado para garantir a comunicação.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A arquitetura de rede HomeKit, que permite a integração de dispositivos de diferentes fabricantes sem a necessidade de um gateway centralizado obrigatório, é baseada em um modelo de **rede ad-hoc** (ou **rede de dispositivos conectados**).  #### Componente Principal: O componente principal da arquitetura HomeKit é o **HomeKit**, que é um sistema de software que permite a comunicação entre dispositivos de diferentes fabricantes. O HomeKit utiliza o protocolo **Matter** (Matter over IP) para garantir a interoperabilidade entre dispositivos.  #### Agrupamento de Dispositivos: Os dispositivos são agrupados em **grupos** (clusters) para implementar uma solução. Cada grupo é composto por dispositivos que compartilham a mesma funcional |
| **Pós-SFT (LoRA)** | O componente principal de uma rede HomeKit é o hub, que atua como o ponto de partida para a configuração da rede. Os dispositivos são agrupados em centros de controle (homes) por meio de grupos de dispositivos. A implementação de uma solução HomeKit não requer um gateway centralizado, sendo possível configurar a rede diretamente no hub, embora a integração com serviços da Apple Cloud possa ser facilitada através desse ponto de acesso central. |


--- 

### Questão 19
**Pergunta:** No contexto de estruturas de dados lineares, qual é a diferença fundamental entre a implementação estática e dinâmica de um Tipo Abstrato de Dados (TAD) de Pilha, e como essa escolha impacta a alocação de memória durante a execução do programa?

**Resposta de Referência:** *A diferença fundamental reside na forma como a memória é alocada para armazenar os elementos da pilha. Na implementação estática, o tamanho máximo da pilha é definido em tempo de compilação, geralmente utilizando um array com tamanho fixo, o que impede o crescimento além desse limite e pode levar a erros de estouro de pilha (stack overflow) se a quantidade de dados exceder a capacidade prevista. Já na implementação dinâmica, a memória é alocada em tempo de execução (frequentemente via alocação dinâmica de memória ou listas encadeadas), permitindo que a pilha cresça ou diminua conforme a necessidade, adaptando-se ao volume de dados processado, embora isso possa introduzir uma pequena sobrecarga de gerenciamento de memória.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A implementação estática de uma pilha utiliza uma estrutura de dados fixa, como um array, que é alocada na memória antes da execução do programa. Isso significa que o tamanho da pilha é conhecido em tempo de compilação, e a alocação de memória é feita uma vez, independentemente do número de elementos que a pilha irá armazenar.  Já a implementação dinâmica de uma pilha utiliza uma estrutura de dados que é alocada na memória durante a execução do programa, como uma lista encadeada. Isso permite que o tamanho da pilha seja ajustado dinamicamente durante a execução, adaptando-se ao número de elementos que a pilha irá armazenar.  A escolha entre implementação estática |
| **Pós-SFT (LoRA)** | A diferença fundamental reside na forma como a memória é alocada para armazenar os elementos da pilha. Na implementação estática, o tamanho máximo da pilha é definido em tempo de compilação, geralmente utilizando um array com tamanho fixo, o que impede o crescimento além desse limite e pode levar a erros de overflow. Já na implementação dinâmica, a memória é alocada em tempo de execução (geralmente via alocação dinâmica de memória ou listas encadeadas), permitindo que a pilha cresça ou diminua conforme a necessidade, adaptando-se ao volume de dados processado, embora isso possa introduzir uma pequena sobrecarga de gerenciamento de memória. |


--- 

### Questão 20
**Pergunta:** Dado o código `s.find('tigres', 30)` executado na string `s='um tigre, dois tigres, três tigres'`, qual é o resultado retornado e qual é a lógica técnica que justifica esse resultado específico?
**Contexto (Input):** `s='um tigre, dois tigres, três tigres'
código: s.find('tigres', 30)`

**Resposta de Referência:** *O resultado retornado é `-1`. A lógica técnica é que a função `find()` inicia a busca pelo índice especificado (neste caso, 30) até o fim da string. Como a substring 'tigres' não existe na string original (apenas 'tigre' existe), e a busca começa em uma posição onde não há mais ocorrências válidas da substring alvo, a função conclui que a substring não foi encontrada no intervalo de busca e retorna `-1`.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | O resultado retornado é `3`.  A lógica técnica que justifica esse resultado específico é a seguinte:  1.  **Análise da String:** A string `s` contém a sequência de caracteres `'tigres'` três vezes consecutivas:     *   Posição 0: `'um tigre'`     *   Posição 1: `' dois tigres'`     *   Posição 2: `' três tigres'`  2.  **Função `find` do Python:** A função `find` busca a primeira ocorrência de um substrito dentro de uma string. Ela retorna o índice (posição) do primeiro caractere do substrito encontrado.  3. |
| **Pós-SFT (LoRA)** | O resultado retornado é `-1`. A lógica técnica é que a função `find()` inicia a busca pelo índice especificado (neste caso, 30) até o fim da string. Como a substring 'tigres' não existe na string original (apenas 'tigre' existe), e a busca começa em uma posição onde não há mais ocorrências válidas da substring alvo, a função conclui que a substring não foi encontrada no intervalo de busca e retorna `-1`. |


--- 

### Questão 21
**Pergunta:** Qual é a diferença fundamental entre o comportamento de propagação de um 'Trojan horse' (Cavalo de Troia) e um vírus em relação aos arquivos do hospedeiro?

**Resposta de Referência:** *A diferença técnica reside na forma de infecção e propagação: um Trojan horse geralmente reside no computador do usuário e se multiplica atacando outras máquinas na rede, muitas vezes sem infectar diretamente os arquivos do hospedeiro da mesma forma que um vírus. Já um vírus infecta especificamente os arquivos do hospedeiro (por exemplo, quando um arquivo é enviado via e-mail), permitindo que ele se espalhe para outros usuários ao modificar esses arquivos.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A diferença fundamental entre o comportamento de propagação de um 'Trojan horse' e um vírus em relação aos arquivos do hospedeiro é que um Trojan horse geralmente não se propaga automaticamente através de arquivos do hospedeiro, mas sim através de um vetor de ataque externo, como um e-mail malicioso, um link infectado ou uma página web comprometida. O Trojan horse é introduzido no sistema de forma explícita, muitas vezes através de um arquivo executável que o usuário executa, e sua propagação ocorre quando o usuário abre o arquivo ou o executa.  Por outro lado, um vírus, por sua vez, é projetado para se propagar automaticamente através de arquivos do hospede |
| **Pós-SFT (LoRA)** | A diferença fundamental reside na forma de infecção e propagação: um Trojan horse geralmente se instala no sistema do usuário e pode se propagar através de conexões de rede ou execução de arquivos, mas não necessariamente se replica automaticamente de todos os arquivos do hospedeiro de forma sistemática como um vírus. Já um vírus é definido por sua capacidade de se anexar a arquivos específicos (como executáveis ou documentos) e, ao serem executados, infectar esses arquivos, frequentemente propagando-se entre computadores conectados à rede. |


--- 

### Questão 22
**Pergunta:** Em um protocolo de controle de acesso ao canal baseado em turnos de fala, qual é a hierarquia de regras aplicada para determinar quem fala a seguir, considerando a recusa do ouvinte em aceitar a oferta de palavra?

**Resposta de Referência:** *A hierarquia de regras aplicada é a seguinte: Primeiro, a Regra 1 é acionada, onde o falante corrente solicita a palavra ao próximo (fazendo uma pergunta, opinião ou pedido). Se o ouvinte rejeitar essa oferta, aplica-se a Regra 2, onde outra pessoa decide iniciar a fala. Caso a Regra 2 não seja acionada (ou seja, ninguém mais se voluntaria), aplica-se a Regra 3, onde o falante corrente continua falando. Essas regras são executadas recursivamente até que um novo turno de fala seja estabelecido.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | <think> Vamos analisar a situação:  O protocolo de controle de acesso ao canal baseado em turnos de fala (como o protocolo de turnos de fala de um canal de comunicação) geralmente segue uma hierarquia de regras para decidir quem fala a seguir. A recusa do ouvinte em aceitar a oferta de palavra pode afetar a ordem de fala.  Em muitos protocolos, a hierarquia de regras pode incluir:  1. **Regra de prioridade**: Se um usuário tem uma prioridade mais alta (por exemplo, baseado em um número de prioridade ou em um protocolo de prioridade), ele fala primeiro. 2. **Regra de turno**: Se não houver prioridade, o usuário que está no turno (ou que |
| **Pós-SFT (LoRA)** | A hierarquia de regras segue a ordem inversa da menção: primeiro, verifica-se se o ouvinte aceita a oferta de palavra; se não aceitar, o sistema avança para verificar se o sistema possui um turno de fala disponível; se não houver turno, o sistema verifica se há um ouvinte disponível que não tenha falado recentemente; finalmente, se nenhum dos anteriores for verdadeiro, o sistema avança para verificar se o sistema possui um turno de fala disponível. |


--- 

### Questão 23
**Pergunta:** Qual é a função principal de um algoritmo de consenso distribuído, como o Paxos ou o Raft, em um cluster de servidores, e por que ele é essencial para a integridade dos dados em ambientes onde falhas são esperadas?

**Resposta de Referência:** *A função principal de um algoritmo de consenso distribuído, como Paxos ou Raft, é garantir que todos os nós de um cluster distribuído concordem sobre um único estado compartilhado ou sobre a ordem das operações, mesmo na presença de falhas de hardware ou de rede. Em ambientes onde falhas são esperadas, esses algoritmos são essenciais para a integridade dos dados porque impedem que o sistema entre em estados inconsistentes ou divergentes. Eles asseguram que, se uma operação de escrita for aceita por uma maioria de nós, ela será replicada e confirmada em todos os nós saudáveis, permitindo que o sistema continue operando corretamente (Disponibilidade) e mantenha a consistência dos dados (Consistência) após a recuperação da falha, cumprindo assim dois dos três requisitos do Teorema CAP.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A função principal de um algoritmo de consenso distribuído, como o Paxos ou o Raft, em um cluster de servidores é garantir que todos os nós do cluster concordem sobre um valor único e consistente, mesmo na presença de falhas. Isso é essencial para a integridade dos dados em ambientes onde falhas são esperadas, pois permite que o sistema continue operando corretamente e forneça respostas consistentes aos clientes, mesmo quando alguns nós falham.  ### Exemplo de Entrada: Um cluster de servidores está sendo implementado para um sistema de banco de dados distribuído. O sistema deve garantir que todos os nós concordem sobre as transações de dados, mesmo em caso de falhas.  ### Res |
| **Pós-SFT (LoRA)** | A função principal de um algoritmo de consenso distribuído, como Paxos ou Raft, é garantir que todos os nós de um cluster distribuído concordem sobre um único estado ou sequência de operações, mesmo na presença de falhas de hardware ou de rede. Em ambientes onde falhas são esperadas, esses algoritmos são essenciais para a integridade dos dados porque asseguram a consistência forte (ACID) em sistemas transacionais distribuídos. Eles impedem que o cluster entre em estados inconsistentes ou divergentes, permitindo que o sistema continue operando corretamente após uma falha, reconstruindo o estado consenso e garantindo que as transações sejam executadas em ordem e que os dados refletam |


--- 

### Questão 24
**Pergunta:** No contexto do algoritmo de ordenação por inserção, qual é a fórmula matemática para calcular o número de comparações no pior caso para um vetor de tamanho n, e qual é a complexidade assintótica correspondente?

**Resposta de Referência:** *Para o pior caso, onde o vetor está ordenado de forma decrescente (ex: 5, 4, 3, 2, 1), o número de comparações C(n) é dado pela soma da progressão aritmética de 1 até n-1, resultando na fórmula C(n) = (n² - n) / 2. A complexidade assintótica correspondente é O(n²), classificada como um custo quadrático.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A fórmula matemática para calcular o número de comparações no pior caso para um vetor de tamanho \( n \) no algoritmo de ordenação por inserção é:  \[ \sum_{i=1}^{n-1} i = \frac{n(n-1)}{2} \]  A complexidade assintótica correspondente é \( O(n^2) \).  ### Explicação: No algoritmo de ordenação por inserção, cada elemento do vetor é comparado com os elementos anteriores até que ele seja colocado na posição correta. No pior caso, cada elemento precisa ser comparado com todos os elementos anteriores, resultando em um total de comparações.  Para um vetor de tamanho |
| **Pós-SFT (LoRA)** | Para o pior caso, onde o vetor está ordenado de forma decrescente (ex: 5, 4, 3, 2, 1), o número de comparações C(n) é dado pela soma da progressão aritmética de 1 até n-1, resultando na fórmula C(n) = (n² - n) / 2. A complexidade assintótica correspondente é O(n²), classificada como um custo quadrático. |


--- 

### Questão 25
**Pergunta:** Explique a relação entre a qualidade dos atores (desenvolvedores ou arquitetos de software) e a credibilidade das histórias (casos de uso ou requisitos) em um projeto de desenvolvimento de software, e como a combinação de ambos pode levar a um resultado descrito como 'lame' (fraco).

**Resposta de Referência:** *Em engenharia de software, a credibilidade de um projeto depende diretamente da competência técnica dos desenvolvedores ('atores') e da viabilidade dos requisitos ou casos de uso ('histórias'). Se os desenvolvedores são altamente qualificados mas trabalham com requisitos fantasiosos, incompreensíveis ou mal definidos ('histórias inacreditáveis'), o resultado final tende a ser um sistema funcional mas inútil ou de baixa qualidade ('lame'). A sinergia entre profissionais competentes e requisitos sólidos é essencial para evitar produtos que, embora tecnicamente possíveis, falham em entregar valor real ou resolvem problemas que não existem.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A relação entre a qualidade dos atores e a credibilidade das histórias é fundamental para o sucesso de um projeto de desenvolvimento de software. A qualidade dos atores, ou seja, a capacidade dos desenvolvedores e arquitetos de software de entender e implementar as histórias de forma eficaz, é crucial para garantir que as histórias sejam realizadas corretamente e de acordo com os requisitos.  Acredibilidade das histórias refere-se à capacidade de as histórias serem compreendidas e implementadas pelos atores, e também à capacidade de as histórias serem realizadas corretamente e de acordo com os requisitos.  A combinação de ambos pode levar a um resultado descrito como 'lame' (fraco) quando há uma falha na comunicação entre os atores |
| **Pós-SFT (LoRA)** | A qualidade dos atores refere-se à competência técnica e à profundidade da compreensão do domínio do desenvolvedor ou arquiteto. A credibilidade das histórias refere-se à viabilidade e à relevância dos requisitos ou casos de uso apresentados. Quando ambos são altos, o resultado tende a ser robusto. No entanto, se os atores forem técnicos mas as histórias forem superficiais, genéricas ou não testadas, o produto final pode ser tecnicamente possível, mas funcionalmente fraco ou não resolvendo problemas reais. A combinação de 'atores bons' com 'histórias fracas' resulta em um sistema que pode ser executável, mas que carece de valor prático, aderência a padrões ou capacidade de escalar, caracterizando |


--- 
