# Relatório de Avaliação do Ajuste Fino Supervisionado (SFT) — Q2 & Q3

Este relatório compara as respostas fornecidas pelo modelo base original vs o modelo após o ajuste fino de instruções (SFT).

- **Modelo Base:** `Qwen/Qwen3.5-2B-Base`
- **Adaptador SFT:** `./q2_sft_model`
- **Total de Casos no Benchmark:** 25

## 📈 Métricas Quantitativas (Split de Teste)

| Métrica | Modelo Baseline | Modelo Pós-SFT | Comparativo |
|---|---|---|---|
| **Loss (Cross-Entropy)** | 1.9233 | 1.2268 | -0.6966 (MELHOROU) |
| **Perplexidade (PPL)** | 6.8436 | 3.4101 | -3.4335 (MELHOROU) |

---

## 📝 Avaliação Qualitativa Lado a Lado

### Questão 1
**Pergunta:** Dado um conjunto de voos com restrições de tempo de conexão mínima de 1 hora e um orçamento limitado, qual é a estratégia algorítmica mais adequada para encontrar o caminho de menor custo entre duas cidades, e como os dados de partida, chegada e custo devem ser estruturados para alimentar esse algoritmo?

**Resposta de Referência:** *A estratégia algorítmica mais adequada é a aplicação do Algoritmo de Dijkstra, que resolve o problema do caminho mais curto em grafos com pesos não negativos. Para estruturar os dados, deve-se modelar as cidades como nós (vértices) e os voos como arestas ponderadas pelo custo financeiro. A restrição de conexão mínima de 1 hora deve ser tratada como uma condição de pré-processamento ou como um peso infinito para arestas que não satisfazem o intervalo entre a chegada em um nó intermediário e a partida do próximo nó, garantindo que apenas conexões válidas sejam consideradas na busca pelo caminho de menor custo total.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | Para encontrar o caminho de menor custo entre duas cidades com restrições de tempo de conexão mínima de 1 hora e um orçamento limitado, a estratégia algorítmica mais adequada é o **Algoritmo de Dijkstra**. Este algoritmo é ideal para encontrar o caminho mais curto em um grafo ponderado, onde os pesos representam os custos (como tempo ou dinheiro).  #### Estrutura dos Dados: 1. **Partida (Departure):**    - Cidade de origem.    - Hora de partida.    - Custo de partida (se aplicável).  2. **Chegada (Arrival):**    - Cidade de destino.    - Hora de chegada.    - Custo de chegada (se aplic |
| **Pós-SFT (LoRA)** | A estratégia algorítmica mais adequada é o Algoritmo de Dijkstra, que resolve o problema do caminho mais curto em grafos com pesos não negativos. Para estruturar os dados, deve-se modelar as cidades como vértices e as rotas como arestas com pesos representando o custo total (tempo de viagem + custo de combustível). Os dados devem ser organizados em uma matriz de adjacência ou lista de adjacência, onde cada nó possui informações de partida, chegada e custo, permitindo que o algoritmo processe as restrições de conexão e o orçamento de forma eficiente. |


--- 

### Questão 2
**Pergunta:** Qual é a forma verbal correta para a primeira pessoa do plural do futuro do presente do verbo 'correr', considerando as regras de acentuação e conjugação padrão em português?

**Resposta de Referência:** *A forma verbal correta é 'correremos'. Esta conjugação pertence ao futuro do presente do indicativo, na primeira pessoa do plural, mantendo a terminação regular '-emos' do verbo 'correr' sem alterações fonéticas ou ortográficas adicionais, diferentemente de formas como 'correrão' (terceira pessoa do singular) ou 'correremos' (primeira pessoa do plural).*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A forma verbal correta para a primeira pessoa do plural do futuro do presente do verbo 'correr' é:  **Corremos**  ### Explicação: - **Futuro do presente**: O futuro do presente do verbo 'correr' é formado com a conjugação 'corremos'. - **Acentuação**: Como o verbo 'correr' é um verbo de segunda conjugação (termina em -er), a forma verbal 'corremos' não recebe acento agudo no 'e', pois a regra de acentuação no futuro do presente para verbos de segunda conjugação é que o 'e' não é acentuado.  Portanto, a resposta correta é **Corremos |
| **Pós-SFT (LoRA)** | O verbo 'correr' é uma raiz inalterada no futuro do presente (futuro simples), pois não possui acento agudo na raiz principal (como em 'correr' vs 'correremos'). A forma correta para a primeira pessoa do plural é 'correremos', mantendo a grafia da raiz sem acento, seguido do sufixo '-emos'. |


--- 

### Questão 3
**Pergunta:** O que é a anomalia de Belady e como ela afeta o desempenho de um sistema que utiliza o algoritmo FIFO de substituição de páginas?

**Resposta de Referência:** *A anomalia de Belady é uma deficiência específica do algoritmo FIFO (First-in, First-out) onde a quantidade de faltas de páginas pode aumentar quando o tamanho da memória também aumenta. Isso ocorre porque o FIFO substitui a página que foi carregada há mais tempo, independentemente de sua utilidade futura, o que pode levar à evicção de páginas frequentemente utilizadas em favor de páginas que não serão acessadas novamente, prejudicando o desempenho do sistema.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A anomalia de Belady é um fenômeno que ocorre em sistemas operacionais que utilizam o algoritmo de substituição de páginas FIFO (First-In, First-Out). Ela se refere à situação em que o número de páginas de página que precisam ser substituídas aumenta quando o número de páginas de página disponíveis aumenta. Isso pode levar a um aumento no número de missas de página, o que, por sua vez, pode resultar em um aumento no tempo de resposta e no consumo de recursos do sistema.  A anomalia de Belady afeta o desempenho de um sistema que utiliza o algoritmo FIFO de substituição de páginas de várias maneiras:  1. **Aumento no número de missas de página**: Quando o número de |
| **Pós-SFT (LoRA)** | A anomalia de Belady ocorre quando, em um sistema que utiliza o algoritmo FIFO (First-In, First-Out) para substituição de páginas, o número de páginas faltantes (page faults) aumenta quando um novo página é alocada, em vez de diminuir. Isso acontece porque o algoritmo FIFO não considera o futuro, podendo substituir uma página que será necessária no futuro, enquanto mantém uma página que não será usada até que uma página mais antiga (e, portanto, mais necessária) seja substituída. |


--- 

### Questão 4
**Pergunta:** Como são classificadas a fila e a pilha em relação à estrutura de dados lista, e qual é a característica fundamental que diferencia a operação de uma fila da de uma pilha?

**Resposta de Referência:** *A fila e a pilha são consideradas casos especiais da lista. A característica fundamental que as diferencia é que, numa fila, a inserção e a retirada são realizadas em extremos opostos (FIFO), enquanto numa pilha, ambas as operações ocorrem no mesmo extremo (LIFO).*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A fila e a pilha são estruturas de dados que podem ser classificadas como **linhas** e **pilhas**, respectivamente, em relação à estrutura de dados **lista**.  - **Fila**: É uma estrutura de dados que segue o princípio do **FIFO** (First In, First Out), ou seja, o primeiro elemento que entra na fila é o primeiro a sair. - **Pilha**: É uma estrutura de dados que segue o princípio do **LIFO** (Last In, First Out), ou seja, o último elemento que entra na pilha é o primeiro a sair.  A característica fundamental que diferencia a operação de uma fila da de uma pilha é o **princípio de ordenação**: |
| **Pós-SFT (LoRA)** | A fila e a pilha são classificadas como estruturas de dados listas. A característica fundamental que as diferencia é a ordem de acesso: na fila, as operações de inserção e remoção ocorrem em extremos opostos (FIFO - First In First Out), enquanto na pilha, as operações ocorrem apenas no extremo mais recente (LIFO - Last In First Out). |


--- 

### Questão 5
**Pergunta:** Descreva os dois critérios de decisão utilizados no algoritmo de redução ao primeiro octante para determinar se é necessário trocar as coordenadas x e y ou substituir valores por seus simétricos.

**Resposta de Referência:** *O algoritmo utiliza dois testes lógicos: 1) Verifica-se se o produto dos incrementos (Δx * Δy) é negativo; se for, substituem-se os valores de y pelos simétricos e marca-se o flag 'simétrico' como verdadeiro. 2) Verifica-se se o valor absoluto de Δx é menor que o valor absoluto de Δy; se for, trocam-se as coordenadas x e y de cada extremo, trocam-se os valores de Δx e Δy, e marca-se o flag 'declive' como verdadeiro.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | O algoritmo de redução ao primeiro octante utiliza dois critérios de decisão para determinar se é necessário trocar as coordenadas x e y ou substituir valores por seus simétricos. Esses critérios são:  1. **Critério de Troca de Coordenadas x e y**:    - Este critério é aplicado quando a coordenada x é maior que a coordenada y. Nesse caso, a coordenada x é trocada com a coordenada y para garantir que a coordenada x seja menor ou igual à coordenada y.    - **Exemplo**: Se a coordenada x é 5 e a coordenada y é 3, então a coordenada x é trocada com a coordenada y, resultando em x |
| **Pós-SFT (LoRA)** | O algoritmo utiliza dois critérios para decidir sobre a troca de coordenadas ou a substituição por simétricos: 1) Se a soma dos valores de x e y for igual a zero (x + y = 0), indicando que os valores estão em relação à origem de forma simétrica, o algoritmo troca as coordenadas x e y. 2) Se o valor de x for negativo, indicando que a posição está à esquerda do eixo y, o algoritmo substitui o valor de x pelo seu simétrico (ou seja, multiplica por -1). |


--- 

### Questão 6
**Pergunta:** Qual é o impacto da complexidade dos módulos do padrão de codificação de vídeo H.264/AVC na implementação puramente por software para vídeos em alta definição, como Full HD (1920×1080 pixels), e qual taxa de quadros é alcançada sob essas condições?

**Resposta de Referência:** *A alta complexidade dos módulos do padrão H.264/AVC torna difícil alcançar taxas de tempo real, como 30 quadros por segundo, em implementações puramente por software, especialmente quando se processam vídeos em alta definição. No entanto, é possível atingir uma taxa de 38 quadros por segundo ao processar quadros Full HD (1920×1080 pixels), desde que se utilize uma largura de banda de memória externa de aproximadamente 299 Mbytes por segundo.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A complexidade dos módulos do padrão de codificação de vídeo H.264/AVC, especialmente em relação à implementação puramente por software para vídeos em alta definição, como Full HD (1920×1080 pixels), tem um impacto significativo na eficiência e no desempenho do processamento.  #### Impacto da Complexidade: 1. **Complexidade Computacional**:    - O H.264/AVC é um padrão de codificação de vídeo altamente eficiente, mas sua complexidade computacional é alta, especialmente em comparação com codecs mais simples como MPEG-2.    - A implementação puramente por software requer mais recursos computacionais, como processamento de cores, transformadas de wave |
| **Pós-SFT (LoRA)** | A complexidade dos módulos do padrão H.264/AVC torna a implementação puramente por software inviável para vídeos em alta definição, como Full HD (1920×1080 pixels), devido ao tempo de execução excessivo. Sob essas condições, a implementação por software resulta em uma taxa de quadros extremamente baixa, de apenas 1 quadro por segundo. |


--- 

### Questão 7
**Pergunta:** Em um cenário de execução de instruções onde múltiplas instruções em uma estação de reserva (reservation station) estão prontas para execução em um mesmo ciclo de máquina, qual é o critério de seleção padrão utilizado por um algoritmo de agendamento para escolher qual instrução será emitida para a unidade funcional?

**Resposta de Referência:** *O critério de seleção padrão utilizado é a política 'oldest first' (primeiro a chegar, primeiro a ser atendido), onde a instrução mais antiga na estação de reserva é escolhida para ser emitida e iniciar sua execução na unidade funcional.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | O critério de seleção padrão utilizado por um algoritmo de agendamento para escolher qual instrução será emitida para a unidade funcional é o **critério de latência**.  ### Explicação: O critério de latência é o mais comum em algoritmos de agendamento de instruções. Ele considera a latência (tempo de execução) de cada instrução e escolhe a instrução com a menor latência para ser executada primeiro. Isso ajuda a minimizar o tempo total de execução da estação de reserva.  ### Exemplo: Suponha que temos três instruções prontas para execução: - Instrução A: latência = 10 ciclos - Instrução B: latência = |
| **Pós-SFT (LoRA)** | O critério de seleção padrão é a 'primeiro em primeiro lido' (First In First Out - FIFO), onde a instrução que foi carregada para a estação de reserva mais recentemente é a que é emitida para a execução. |


--- 

### Questão 8
**Pergunta:** Qual é a função principal do Scrum Master no contexto da implementação do processo Scrum?

**Resposta de Referência:** *A função principal do Scrum Master é garantir o uso correto do processo Scrum e eliminar interferências externas que possam atrapalhar o fluxo de trabalho da equipe.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | O Scrum Master tem a função principal de garantir que o processo Scrum seja implementado e mantido de forma eficaz. Isso inclui:  - Facilitar a comunicação entre os membros da equipe e o Product Owner. - Garantir que a equipe siga as práticas e regras do Scrum. - Remover impedimentos que possam atrapalhar a equipe. - Ajudar a equipe a se adaptar às mudanças e a melhorar continuamente. - Promover uma cultura de transparência e colaboração.  ### Resposta: O Scrum Master tem a função principal de garantir que o processo Scrum seja implementado e mantido de forma eficaz. Isso inclui:  - Facilitar a comunicação entre os membros da |
| **Pós-SFT (LoRA)** | O Scrum Master atua como um facilitador e treinador, responsável por garantir que a equipe esteja implementando corretamente o processo Scrum, removendo obstáculos e impedimentos que possam atrapalhar o fluxo de trabalho, e promovendo uma cultura de melhoria contínua baseada nos princípios do Scrum. |


--- 

### Questão 9
**Pergunta:** Quais são as principais vantagens e desvantagens associadas ao uso de variáveis locais em subprogramas, como em C e Java, em comparação com variáveis dinâmicas do monte?

**Resposta de Referência:** *As variáveis locais em subprogramas (como em C e Java) oferecem a vantagem de permitir a recursão e conservar o armazenamento, pois suas alocações são estáticas e vinculadas à declaração. No entanto, apresentam desvantagens como sobrecarga na alocação e liberação de memória, referências ineficientes devido ao endereçamento indireto, e o fato de os subprogramas não serem sensíveis ao histórico de execução. Em contraste, as variáveis dinâmicas do monte (heap) são anônimas, referenciadas apenas por ponteiros, e exigem alocação e liberação explícitas, o que prevê um gerenciamento de armazenamento dinâmico, mas impõe a desvantagem de exigir gerenciamento manual ou automático (como garbage collection) para evitar vazamentos de memória.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | Aqui está uma resposta completa que aborda a comparação entre variáveis locais e variáveis dinâmicas do monte, explicando as vantagens e desvantagens de cada abordagem:  ---  ### **Vantagens e Desvantagens das Variáveis Locais em Subprogramas**  #### **1. Variáveis Locais em Subprogramas (C e Java)** - **O que são**: Variáveis locais são declaradas dentro de um bloco de código (como um subprograma ou função) e têm vida útil limitada a esse bloco. - **Vantagens**:   1. **Isolamento de Dados**: As variáveis locais não afetam o estado global do programa, reduzindo o risco |
| **Pós-SFT (LoRA)** | As principais vantagens das variáveis locais são que elas são sempre disponíveis e não precisam ser declaradas antes do uso, o que permite a compilação mais rápida. As desvantagens incluem que elas são destruídas quando o subprograma termina, o que pode levar a erros de memória se o código for executado mais de uma vez, e que o tamanho do programa aumenta devido ao armazenamento de cada variável local. |


--- 

### Questão 10
**Pergunta:** Quais são as três principais desvantagens associadas ao uso do algoritmo de marcação-varrer (mark-sweep) para gerenciamento de memória, especificamente relacionadas à frequência da execução, ao impacto na performance e à complexidade de implementação?

**Resposta de Referência:** *As três principais desvantagens são: 1) A coleta de lixo é realizada com pouca frequência, o que pode levar à fragmentação de memória; 2) Quando executada, o processo causa atrasos significativos na execução da aplicação devido à sobrecarga de CPU; 3) A implementação é complexa, pois requer a configuração inicial de indicadores para todas as células, um processo de marcação não trivial e a manutenção de uma lista de espaços disponíveis, além de lidar com dificuldades específicas de gerenciamento de montes para células de tamanho único.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | O algoritmo de marcação-varrer (mark-sweep) é uma técnica de gerenciamento de memória que combina a marcação (marking) de blocos de memória não utilizados com a varrer (sweeping) de blocos marcados para liberação. Embora seja uma abordagem simples e eficiente, ele apresenta algumas desvantagens significativas:  1. **Frequência da Execução**: O algoritmo de marcação-varrer pode ser computacionalmente intensivo, especialmente em sistemas com muitos processos ou memória compartilhada. A marcação de todos os blocos de memória não utilizados pode levar a um alto custo de tempo de execução, o que pode ser problemático em sistemas com restrições de tempo de resposta.  2 |
| **Pós-SFT (LoRA)** | As três principais desvantagens são: 1) O algoritmo é executado frequentemente, o que pode levar a uma degradação significativa no desempenho do sistema; 2) Ele é uma técnica de gerenciamento de memória não otimizada, resultando em um desempenho inferior em comparação a outras abordagens; e 3) A implementação do algoritmo é complexa, exigindo mecanismos adicionais para garantir a correção e a eficiência. |


--- 

### Questão 11
**Pergunta:** Quais são as três arquiteturas de clusterização de aplicações web mais comuns e como elas diferem em termos de disponibilidade dos nós para atender solicitações de clientes?

**Resposta de Referência:** *As três arquiteturas mais comuns são: 1) Ativa-ativa, onde todos os nós do cluster estão ativos e atendem simultaneamente às solicitações; 2) Ativa-passiva, onde apenas um nó está ativo atendendo aos clientes, enquanto os demais ficam em modo de espera para assumir o controle em caso de falha do nó ativo; e 3) Multimestre, onde vários nós podem estar ativos ao mesmo tempo para processar as requisições.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | As três arquiteturas de clusterização de aplicações web mais comuns são:  1. **Clusterização de Aplicação (Application Clustering)**:    - **Descrição**: Neste modelo, todas as aplicações são colocadas em um único cluster. Isso significa que todas as requisições de clientes são processadas por um único nó.    - **Disponibilidade de Nós**: Todos os nós estão disponíveis para atender solicitações de clientes. No entanto, se um nó falhar, toda a aplicação fica indisponível, pois não há redundância.    - **Vantagens**: Simplicidade e baixo custo de implementação.    - **Desvantagens**: Alta disponibilidade é comprometida, pois a falha de um |
| **Pós-SFT (LoRA)** | As três arquiteturas mais comuns são: 1) Clusterização de aplicação, onde todos os nós da aplicação são responsáveis por atender os clientes; 2) Clusterização de aplicação com disponibilidade, onde todos os nós são responsáveis, mas a aplicação possui mecanismos para manter a disponibilidade; e 3) Clusterização de aplicação com disponibilidade e escalabilidade, onde a aplicação possui mecanismos para manter a disponibilidade e a escalabilidade. |


--- 

### Questão 12
**Pergunta:** Qual é a principal propriedade estrutural que define o modelo matemático de uma lista, conforme a definição técnica apresentada?

**Resposta de Referência:** *A principal propriedade estrutural de uma lista é a posição relativa dos elementos dentro da sequência linear.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A principal propriedade estrutural que define o modelo matemático de uma lista, conforme a definição técnica apresentada, é a **estrutura de dados** que permite armazenar e manipular elementos de forma sequencial. Essa estrutura é caracterizada por:  1. **Elementos**: Cada elemento da lista é um item que pode ser de qualquer tipo (por exemplo, números, strings, objetos, etc.). 2. **Posição**: Os elementos são organizados em uma sequência linear, onde cada elemento tem uma posição única e pode ser acessado por meio de um índice ou posição. 3. **Operações**: A lista suporta operações como inserção, remoção, busca e iteração, que são definidas de maneira precisa e formal |
| **Pós-SFT (LoRA)** | A principal propriedade estrutural que define uma lista é a existência de uma operação de concatenação (ou composição) que permite unir duas listas de forma única e previsível, resultando em uma nova lista, enquanto a estrutura interna de cada lista é representada por um elemento e uma lista subsequente. |


--- 

### Questão 13
**Pergunta:** Calcule a diferença de pontuação entre a coluna P1 e a coluna P2 para o registro que possui o maior valor absoluto de diferença entre essas duas métricas de desempenho, considerando apenas os registros onde ambos os valores estão presentes.
**Contexto (Input):** `20219003210 10,0 10,0 - 20199015656 10,0 8,0 - 20199013179 10,0 8,0 - 20199028126 10,0 7,5 - 20199041496 10,0 8,5 - 2013956383 - - - 20199054073 7,6 7,0 - 20199012716 8,8 9,5 - 20199000985 8,4 9,0 - 20199010936 10,0 8,0 - 20199006030 7,2 8,0 - 20169062987 8,2 - - 20199022534 10,0 9,5 - 20199008114 10,0 7,5 - 20199022801 9,5 5,0`

**Resposta de Referência:** *O registro com maior diferença absoluta é o identificado por 20199022801, que apresenta 9,5 na coluna P1 e 5,0 na coluna P2. A diferença calculada é de 4,5 pontos (9,5 - 5,0 = 4,5).*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | <think> Vamos analisar a instrução:  - Precisamos calcular a diferença de pontuação entre a coluna P1 e a coluna P2 para o registro que possui o maior valor absoluto de diferença entre essas duas métricas de desempenho. - Considerar apenas os registros onde ambos os valores estão presentes (ou seja, onde P1 e P2 são ambos preenchidos). - A entrada é uma lista de registros, cada um com 5 colunas: ID, P1, P2, P3, P4.  Vamos extrair os registros onde P1 e P2 estão presentes (não vazios). A entrada tem:  1. 20219003210 10,0 |
| **Pós-SFT (LoRA)** | O registro com o maior valor absoluto de diferença entre P1 e P2 é o registro 20199003210, que possui uma diferença de 0,0 (10,0 - 10,0). No entanto, se considerarmos a diferença absoluta entre as colunas P1 e P2 para todos os registros onde ambos estão definidos, o registro 20199003210 tem a diferença de 0,0. O registro com a maior diferença absoluta entre as colunas P1 e P2 (considerando a diferença entre os valores de P1 e P2 de pares distintos) é o registro 20199003 |


--- 

### Questão 14
**Pergunta:** Em C, ao utilizar a função scanf para ler dois valores de ponto flutuante em um único campo de formato, qual é a sintaxe correta para o argumento de formato e quais são as implicações de segurança e precisão ao comparar esses valores diretamente com zero usando o operador de igualdade (==)?
**Contexto (Input):** `scanf("%f%f", &p.x, &p.y);`

**Resposta de Referência:** *A sintaxe correta para ler dois valores de ponto flutuante em uma única chamada é usar o formato "%f%f" (ou "%f %f"), onde cada conversão especifica um endereço de variável. A comparação direta de valores de ponto flutuante com zero (ou qualquer outro número) usando o operador == é tecnicamente problemática devido à natureza binária da representação de ponto flutuante (IEEE 754), que pode introduzir erros de arredondamento mínimos. Embora a comparação com zero exato seja geralmente segura (pois zero tem representação exata), em cenários de cálculos complexos, recomenda-se verificar se o valor está dentro de uma margem de erro (epsilon) em vez de exigir igualdade exata.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A sintaxe correta para o argumento de formato é `"%f%f"`. No entanto, é importante notar que a função `scanf` não possui um argumento de formato para especificar o número de dígitos após a vírgula. Portanto, a entrada fornecida `scanf("%f%f", &p.x, &p.y);` é válida, mas não garante que os valores lidos sejam exatamente de ponto flutuante simples (float) ou de ponto flutuante de precisão dupla (double).  Ao comparar os valores diretamente com zero usando o operador de igualdade (`==`), há implicações de segurança e precisão:  1. **Precisão**: O operador `==` compara os valores exatos |
| **Pós-SFT (LoRA)** | A sintaxe correta para ler dois valores de ponto flutuante em um único formato é "%f%f". A comparação direta com zero usando o operador == é insegura e pode resultar em falsos positivos devido à imprecisão finita da representação binária de números decimais em memória, exigindo comparações com uma tolerância (epsilon) ou verificação de não-nulidade. |


--- 

### Questão 15
**Pergunta:** Quais são as características físicas e de posicionamento que permitem a operação dos 'smart dust motes' em ambientes específicos?

**Resposta de Referência:** *Devido ao seu pequeno tamanho e leve peso, os 'smart dust motes' podem ser anexados a objetos ou até mesmo flutuar no ar, permitindo uma versatilidade de posicionamento que difere de redes de sensores convencionais.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | Os 'smart dust motes' são dispositivos microscópicos projetados para operar em ambientes específicos, como ambientes de laboratório, ambientes de pesquisa, ou ambientes de monitoramento ambiental. Suas características físicas e de posicionamento são projetadas para permitir que eles operem de forma eficiente e precisa em ambientes específicos.  ### Características Físicas: Os 'smart dust motes' são dispositivos microscópicos, geralmente com dimensões de alguns micrômetros a alguns milímetros. Eles são projetados para serem leves e compactos, permitindo que sejam facilmente manipulados e posicionados em ambientes específicos.  ### Características de Posicionamento: Os 'smart dust motes' são projetados para serem capazes de |
| **Pós-SFT (LoRA)** | Os 'smart dust motes' são dispositivos microscópicos que podem ser posicionados em locais de difícil acesso, como dentro de células, e operam em ambientes com baixa energia. |


--- 

### Questão 16
**Pergunta:** Qual é a origem histórica e o objetivo primário dos projetos que deram origem à tecnologia e conceitos fundamentais da Internet, conforme descrito no contexto de redes de comunicação?

**Resposta de Referência:** *A tecnologia e os conceitos fundamentais da Internet surgiram de projetos conduzidos ao longo dos anos 60 pelo Departamento de Defesa dos Estados Unidos. O objetivo primário desses projetos era o desenvolvimento de uma rede de computadores capaz de facilitar a comunicação entre os principais centros militares de comando e controle.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A resposta deve ser escrita em português, com um tom formal e objetivo, e deve ser estruturada em parágrafos.  A resposta deve ser escrita em português, com um tom formal e objetivo, e deve ser estruturada em parágrafos.  A resposta deve ser escrita em português, com um tom formal e objetivo, e deve ser estruturada em parágrafos.  A resposta deve ser escrita em português, com um tom formal e objetivo, e deve ser estruturada em parágrafos.  A resposta deve ser escrita em português, com um tom formal e objetivo, e deve ser estruturada em parágrafos.  A resposta deve ser escrita em português, com um tom formal e objetivo, |
| **Pós-SFT (LoRA)** | A origem histórica desses projetos remonta à década de 1960, quando foram desenvolvidos para permitir a comunicação entre computadores e entre computadores e outros dispositivos. O objetivo primário era estabelecer as bases tecnológicas e conceituais que formam a internet moderna, focando na interconexão de sistemas computacionais para facilitar o fluxo de informação. |


--- 

### Questão 17
**Pergunta:** Quais são os três principais sistemas de numeração discutidos no contexto da evolução histórica e das características inerentes dos sistemas numéricos em eletrônica digital?

**Resposta de Referência:** *Os três principais sistemas de numeração identificados são o Sistema Decimal, o Sistema Binário e o Sistema Hexadecimal. O texto destaca que esses sistemas possuem características inerentes comuns e descreve a evolução histórica que levou ao desenvolvimento dessas bases numéricas, sendo o binário fundamental para a representação de dados em computadores devido à sua simplicidade na implementação eletrônica (ligado/desligado).*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | Os três principais sistemas de numeração discutidos no contexto da evolução histórica e das características inerentes dos sistemas numéricos em eletrônica digital são:  1. **Sistema Decimal (Base 10)**:    - **Características**: Utiliza os dígitos de 0 a 9.    - **Evolução Histórica**: É o sistema mais utilizado no dia a dia e na vida cotidiana, sendo a base da maioria das culturas humanas.    - **Aplicação em Eletrônica Digital**: Embora não seja o sistema primário em eletrônica digital, é amplamente utilizado em interfaces de usuário e em sistemas que requerem fácil compreensão humana.  2. **Sistema Binário ( |
| **Pós-SFT (LoRA)** | Os três principais sistemas de numeração discutidos são o binário, o hexadecimal e o octal. Esses sistemas são fundamentais para a representação de dados em eletrônica digital, onde o binário (base 2) é a base fundamental devido à natureza binária dos transistores, enquanto o hexadecimal e o octal servem como convenções de abreviatura para facilitar a leitura de grandes quantidades de bits binários. |


--- 

### Questão 18
**Pergunta:** No contexto da arquitetura de rede HomeKit, qual é o componente principal definido e como os dispositivos são agrupados para implementar uma solução, considerando a ausência de um gateway centralizado obrigatório?

**Resposta de Referência:** *O componente principal de uma rede HomeKit é o acessório (dispositivo). Os dispositivos são agrupados com base nos tipos específicos de serviços que eles podem fornecer. A implementação de uma solução HomeKit inicia-se pela ativação de um grupo de serviços previamente definidos, onde os serviços implementam características que definem as interações entre si, permitindo que usuários e dispositivos comuniquem-se diretamente via Siri e aplicativos HomeKit sem a necessidade de um hub centralizado para garantir a comunicação.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A arquitetura de rede HomeKit não exige um gateway centralizado obrigatório, permitindo que os dispositivos sejam agrupados de forma flexível. O componente principal definido é o **HomeKit**, que atua como um sistema de gerenciamento de dispositivos e serviços. Os dispositivos são agrupados em **grupos** (clusters) para implementar soluções específicas, como controle de iluminação, temperatura e segurança. Esses grupos são gerenciados por um **hub** (como o HomePod ou o HomeKit Hub), que atua como um intermediário entre os dispositivos e o usuário. O hub pode ser um dispositivo físico ou um serviço em nuvem, e ele permite que os dispositivos se comuniquem entre si e com o usuário de forma centralizada, sem a necessidade de um |
| **Pós-SFT (LoRA)** | O componente principal definido é o 'HomeKit', que atua como uma camada de abstração para a implementação de uma solução de automação. Os dispositivos são agrupados em 'clusters' para implementar a solução. A arquitetura permite que a solução seja implementada sem a necessidade de um gateway centralizado, utilizando a comunicação via HomeKit. |


--- 

### Questão 19
**Pergunta:** No contexto de estruturas de dados lineares, qual é a diferença fundamental entre a implementação estática e dinâmica de um Tipo Abstrato de Dados (TAD) de Pilha, e como essa escolha impacta a alocação de memória durante a execução do programa?

**Resposta de Referência:** *A diferença fundamental reside na forma como a memória é alocada para armazenar os elementos da pilha. Na implementação estática, o tamanho máximo da pilha é definido em tempo de compilação, geralmente utilizando um array com tamanho fixo, o que impede o crescimento além desse limite e pode levar a erros de estouro de pilha (stack overflow) se a quantidade de dados exceder a capacidade prevista. Já na implementação dinâmica, a memória é alocada em tempo de execução (frequentemente via alocação dinâmica de memória ou listas encadeadas), permitindo que a pilha cresça ou diminua conforme a necessidade, adaptando-se ao volume de dados processado, embora isso possa introduzir uma pequena sobrecarga de gerenciamento de memória.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A implementação estática de uma pilha utiliza uma estrutura de dados fixa, como um array, que é alocada na memória antes da execução do programa. Isso significa que a memória é reservada antecipadamente, e a pilha cresce até o limite superior da estrutura. A alocação de memória é feita antes da execução, o que pode ser vantajoso em termos de previsibilidade e desempenho, mas pode ser ineficiente se a pilha não atingir o limite superior.  Por outro lado, a implementação dinâmica de uma pilha utiliza uma estrutura de dados que cresce durante a execução, como uma lista encadeada. A memória é alocada e liberada dinamicamente, o que permite que a pilha cresça |
| **Pós-SFT (LoRA)** | A diferença fundamental reside na forma como a memória é alocada para o tipo. Na implementação estática, a alocação de memória ocorre na compilação, definindo um tamanho fixo para a pilha (ex: 100 elementos), o que permite acesso rápido mas pode levar a vazamentos de memória se a pilha for maior que o tamanho definido. Na implementação dinâmica, a alocação ocorre na execução, geralmente utilizando uma função de alocação de memória (como `malloc`) para criar o espaço apenas quando necessário, permitindo que a pilha cresça ou diminua conforme a necessidade, mas introduzindo um pequeno overhead de gerenciamento de memória e possível lentidão no acesso devido à verificação de ponteiros. |


--- 

### Questão 20
**Pergunta:** Dado o código `s.find('tigres', 30)` executado na string `s='um tigre, dois tigres, três tigres'`, qual é o resultado retornado e qual é a lógica técnica que justifica esse resultado específico?
**Contexto (Input):** `s='um tigre, dois tigres, três tigres'
código: s.find('tigres', 30)`

**Resposta de Referência:** *O resultado retornado é `-1`. A lógica técnica é que a função `find()` inicia a busca pelo índice especificado (neste caso, 30) até o fim da string. Como a substring 'tigres' não existe na string original (apenas 'tigre' existe), e a busca começa em uma posição onde não há mais ocorrências válidas da substring alvo, a função conclui que a substring não foi encontrada no intervalo de busca e retorna `-1`.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | O resultado retornado é `3`.  A lógica técnica que justifica esse resultado específico é a **busca de substring** (ou subconjunto) dentro de uma string, utilizando o método `find()` da classe `str` do módulo `string` em Python.  Aqui está a explicação detalhada:  1.  **Análise da String:**     A string `s` contém a sequência de caracteres: `u m   t i g r e s ,   d o u s   t i g r e s ,   t r ê s   t i g r e s`.  2.  **Onde a Busca Começa:**     O parâmetro `30` |
| **Pós-SFT (LoRA)** | O resultado retornado é -1. A lógica técnica é que o método `find` busca a primeira ocorrência da substring 'tigres' iniciando a verificação no índice 30. Como a string contém a substring 'tigres' apenas na posição 0, 1 e 2 (respectivamente, 'tigre', 'tigres', 'tigres'), e não há ocorrência na posição 30 ou qualquer posição subsequente até o final da string, o método conclui que não encontrou o substrato e retorna -1, que é o valor padrão para indicar falha na busca. |


--- 

### Questão 21
**Pergunta:** Qual é a diferença fundamental entre o comportamento de propagação de um 'Trojan horse' (Cavalo de Troia) e um vírus em relação aos arquivos do hospedeiro?

**Resposta de Referência:** *A diferença técnica reside na forma de infecção e propagação: um Trojan horse geralmente reside no computador do usuário e se multiplica atacando outras máquinas na rede, muitas vezes sem infectar diretamente os arquivos do hospedeiro da mesma forma que um vírus. Já um vírus infecta especificamente os arquivos do hospedeiro (por exemplo, quando um arquivo é enviado via e-mail), permitindo que ele se espalhe para outros usuários ao modificar esses arquivos.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A diferença fundamental entre o comportamento de propagação de um 'Trojan horse' e um vírus em relação aos arquivos do hospedeiro é que um Trojan horse geralmente não se propaga automaticamente através de arquivos do hospedeiro, mas sim através de um ataque social ou engenharia social, onde o usuário é enganado a executar o arquivo. Por outro lado, um vírus geralmente se propaga automaticamente através de arquivos do hospedeiro, como anexos de e-mail ou downloads, e pode se replicar e se espalhar entre diferentes sistemas. |
| **Pós-SFT (LoRA)** | A diferença fundamental reside na natureza da infecção: um 'Trojan horse' é uma aplicação que se infiltra no sistema para realizar uma tarefa específica (como roubo de dados ou acesso não autorizado), enquanto um vírus é um programa que se replica automaticamente, infectando outros arquivos do hospedeiro para se propagar. |


--- 

### Questão 22
**Pergunta:** Em um protocolo de controle de acesso ao canal baseado em turnos de fala, qual é a hierarquia de regras aplicada para determinar quem fala a seguir, considerando a recusa do ouvinte em aceitar a oferta de palavra?

**Resposta de Referência:** *A hierarquia de regras aplicada é a seguinte: Primeiro, a Regra 1 é acionada, onde o falante corrente solicita a palavra ao próximo (fazendo uma pergunta, opinião ou pedido). Se o ouvinte rejeitar essa oferta, aplica-se a Regra 2, onde outra pessoa decide iniciar a fala. Caso a Regra 2 não seja acionada (ou seja, ninguém mais se voluntaria), aplica-se a Regra 3, onde o falante corrente continua falando. Essas regras são executadas recursivamente até que um novo turno de fala seja estabelecido.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | <think> Vamos analisar a situação:  O protocolo de controle de acesso ao canal baseado em turnos de fala (como o protocolo de turnos de fala de um canal de comunicação) geralmente segue regras para determinar quem fala a seguir. A entrada menciona "recusa do ouvinte em aceitar a oferta de palavra", o que sugere que há uma situação em que um ouvinte não aceita a oferta de falar.  Em protocolos de turnos de fala, há várias regras que podem ser aplicadas, como:  1. **Regra de prioridade**: Se um ouvinte está mais importante ou tem mais direito de falar, ele pode falar mesmo que outro não aceite. 2. **Regra de recusa**: Se um ouv |
| **Pós-SFT (LoRA)** | A hierarquia de regras é aplicada da seguinte forma: primeiro, verifica-se se o ouvinte aceitou a oferta de palavra. Se não houver aceitação, o sistema avança para a segunda regra, que verifica se o ouvinte está em um turno de fala. Se o ouvinte estiver em um turno, ele é obrigado a falar. Caso o ouvinte não esteja em nenhum turno, o sistema avança para a terceira regra, que verifica se o ouvinte está em um turno de fala e, se estiver, ele fala. Se o ouvinte não estiver em nenhum turno, o sistema avança para a quarta regra, que verifica se o ouvinte está em um turno de fala e, se estiver, ele fala. Se o ouv |


--- 

### Questão 23
**Pergunta:** Qual é a função principal de um algoritmo de consenso distribuído, como o Paxos ou o Raft, em um cluster de servidores, e por que ele é essencial para a integridade dos dados em ambientes onde falhas são esperadas?

**Resposta de Referência:** *A função principal de um algoritmo de consenso distribuído, como Paxos ou Raft, é garantir que todos os nós de um cluster distribuído concordem sobre um único estado compartilhado ou sobre a ordem das operações, mesmo na presença de falhas de hardware ou de rede. Em ambientes onde falhas são esperadas, esses algoritmos são essenciais para a integridade dos dados porque impedem que o sistema entre em estados inconsistentes ou divergentes. Eles asseguram que, se uma operação de escrita for aceita por uma maioria de nós, ela será replicada e confirmada em todos os nós saudáveis, permitindo que o sistema continue operando corretamente (Disponibilidade) e mantenha a consistência dos dados (Consistência) após a recuperação da falha, cumprindo assim dois dos três requisitos do Teorema CAP.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A função principal de um algoritmo de consenso distribuído, como o Paxos ou o Raft, em um cluster de servidores é garantir que todos os nós do cluster concordem sobre um único valor ou estado, mesmo na presença de falhas. Isso é essencial para a integridade dos dados em ambientes onde falhas são esperadas, pois permite que o sistema continue funcionando corretamente e mantenha a consistência dos dados entre os nós.  ### Explicação: Em sistemas distribuídos, falhas são inevitáveis. Algoritmos de consenso distribuído, como Paxos e Raft, são projetados para lidar com essas falhas e garantir que todos os nós concordem sobre um único valor. Isso é |
| **Pós-SFT (LoRA)** | A função principal de um algoritmo de consenso distribuído é garantir que todos os nós de um cluster concordem sobre um único valor ou estado, mesmo na presença de falhas parciais ou temporárias de nós. Ele é essencial para a integridade dos dados porque assegura que, após uma falha, o sistema retorne a um estado consistente e correto, evitando que diferentes nós mantenham versões divergentes dos dados, o que poderia levar a corrupção de informações ou comportamentos inconsistentes no sistema. |


--- 

### Questão 24
**Pergunta:** No contexto do algoritmo de ordenação por inserção, qual é a fórmula matemática para calcular o número de comparações no pior caso para um vetor de tamanho n, e qual é a complexidade assintótica correspondente?

**Resposta de Referência:** *Para o pior caso, onde o vetor está ordenado de forma decrescente (ex: 5, 4, 3, 2, 1), o número de comparações C(n) é dado pela soma da progressão aritmética de 1 até n-1, resultando na fórmula C(n) = (n² - n) / 2. A complexidade assintótica correspondente é O(n²), classificada como um custo quadrático.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A fórmula matemática para calcular o número de comparações no pior caso para um vetor de tamanho n no algoritmo de ordenação por inserção é:  \[ \sum_{i=1}^{n-1} i = \frac{n(n-1)}{2} \]  A complexidade assintótica correspondente é \(O(n^2)\).  ### Explicação: No algoritmo de ordenação por inserção, cada elemento do vetor é inserido na posição correta no vetor ordenado. No pior caso, cada elemento precisa ser comparado com todos os elementos anteriores, resultando em um número total de comparações igual à soma dos inteiros de 1 até \(n-1\ |
| **Pós-SFT (LoRA)** | No pior caso, o número de comparações é calculado pela soma de uma progressão aritmética: 1 + 2 + 3 + ... + n. A fórmula resultante é n(n + 1)/2. A complexidade assintótica correspondente é O(n²), indicando que o algoritmo é quadratico. |


--- 

### Questão 25
**Pergunta:** Explique a relação entre a qualidade dos atores (desenvolvedores ou arquitetos de software) e a credibilidade das histórias (casos de uso ou requisitos) em um projeto de desenvolvimento de software, e como a combinação de ambos pode levar a um resultado descrito como 'lame' (fraco).

**Resposta de Referência:** *Em engenharia de software, a credibilidade de um projeto depende diretamente da competência técnica dos desenvolvedores ('atores') e da viabilidade dos requisitos ou casos de uso ('histórias'). Se os desenvolvedores são altamente qualificados mas trabalham com requisitos fantasiosos, incompreensíveis ou mal definidos ('histórias inacreditáveis'), o resultado final tende a ser um sistema funcional mas inútil ou de baixa qualidade ('lame'). A sinergia entre profissionais competentes e requisitos sólidos é essencial para evitar produtos que, embora tecnicamente possíveis, falham em entregar valor real ou resolvem problemas que não existem.*

| Modelo | Resposta Gerada |
|---|---|
| **Baseline** | A relação entre a qualidade dos atores e a credibilidade das histórias é fundamental para o sucesso de um projeto de desenvolvimento de software. A qualidade dos atores, ou seja, os desenvolvedores e arquitetos de software, desempenha um papel crucial na criação de histórias que são precisas, completas e alinhadas com os objetivos do projeto.  Acredibilidade das histórias: As histórias devem ser bem definidas, claras e detalhadas, refletindo as necessidades e expectativas dos atores. Elas devem ser validadas e testadas para garantir que estejam corretas e que atendam aos requisitos do projeto.  Qualidade dos atores: Os desenvolvedores e arquitetos de software devem ter habilidades técnicas e conhecimentos suficientes para |
| **Pós-SFT (LoRA)** | A qualidade dos atores é um fator crítico, mas não suficiente por si só. Se os atores forem de alta qualidade (ex: desenvolvedores experientes) mas as histórias forem de baixa qualidade (ex: requisitos incompletos, ambíguos ou não testáveis), o resultado final tende a ser um produto fraco. A credibilidade das histórias é essencial para guiar o desenvolvimento correto; sem elas, mesmo os melhores desenvolvedores podem construir uma solução que não resolve o problema real, resultando em um sistema 'lame' que falha em atender às necessidades reais dos usuários ou do negócio. |


--- 
