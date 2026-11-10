# Inferência em LLMs: como os modelos de IA geram respostas

## Referência e objetivo

Este resumo estendido acompanha o vídeo [“What is LLM Inference? How AI Models Generate Response”](https://www.youtube.com/watch?v=615-yWyS1n0), que explica como os pesos de um modelo treinado são usados para atender solicitações em tempo real. O texto organiza os pontos apresentados: tokenização, roteamento para GPUs, *batching* contínuo, fases de *prefill* e *decode*, cache KV e métricas de latência, e acrescenta contexto para tornar esses conceitos mais claros.

O texto é uma síntese autoral do vídeo fornecido, não uma transcrição literal. Algumas explicações complementares são incluídas para relacionar os conceitos e qualificar afirmações que dependem do modelo, do hardware e da carga de trabalho.

## 1. O que significa inferência

Um modelo de linguagem de grande porte, ou LLM, é uma rede neural treinada para reconhecer padrões em sequências de texto e estimar quais elementos podem vir a seguir. **Inferência** é a etapa em que um modelo já treinado é usado para processar uma entrada e produzir uma saída. Em um assistente conversacional, a entrada é normalmente a mensagem da pessoa, acompanhada de instruções e, possivelmente, do histórico da conversa. A saída é a resposta gerada.

Inferência não é sinônimo de treinamento. No treinamento, grandes coleções de exemplos são usadas para ajustar os parâmetros do modelo por meio de otimização, processo que exige muitos dados e recursos computacionais. Quando o treinamento termina, os parâmetros aprendidos, os **pesos** ficam armazenados, mas isso não significa que o modelo esteja gerando respostas continuamente. Para responder, é preciso executar esses pesos sobre uma entrada: esse processo é a inferência. Ela acontece a cada solicitação, seja para conversar, resumir um texto, classificar conteúdo ou ajudar a escrever código.

O vídeo ressalta que o treinamento de modelos de fronteira pode custar muito e que a inferência, por ocorrer repetidamente em produção, pode representar um custo acumulado maior ao longo do tempo. Essa comparação não é universal: depende do custo de treinamento, do volume de solicitações, do tamanho dos prompts e respostas e dos recursos usados para servir. O ponto principal é que o custo da inferência se repete com a demanda.

O **motor de inferência** é o software que coordena a execução do modelo e o atendimento às solicitações. Ele administra o uso dos pesos e dos aceleradores, organiza as entradas, agenda o trabalho e busca entregar respostas com confiabilidade, rapidez e capacidade para atender muitos usuários. Assim, inferência não é apenas o cálculo isolado da rede neural: em produção, depende também da infraestrutura que distribui e gerencia esse cálculo.

## 2. Da mensagem aos tokens

O modelo não recebe palavras como unidades humanas de significado. Antes do processamento, um componente chamado **tokenizador** transforma o texto em tokens, que podem representar palavras completas, partes de palavras, pontuação ou outros símbolos. A frase “modelos de linguagem” pode, por exemplo, ser dividida em mais de um token, de acordo com o vocabulário e as regras do tokenizador daquele modelo.

Cada token é mapeado para um ID numérico do vocabulário do modelo e, em seguida, convertido em uma representação numérica que a rede pode processar. O modelo também incorpora informação sobre a posição dos tokens, pois a ordem é importante para interpretar a sequência. Assim, a mensagem e o contexto chegam ao modelo como uma sequência de vetores numéricos, e não como uma cadeia de caracteres simples.

Esse detalhe tem consequências práticas. O limite de contexto de um modelo costuma ser medido em tokens, não em palavras ou páginas. Além disso, o tamanho do prompt (instruções, histórico, documentos fornecidos e pergunta) afeta o trabalho necessário para processar e pode influenciar a latência e o custo.

## 3. Como o Transformer interpreta o contexto

Muitos LLMs atuais são construídos com a arquitetura **Transformer**. Um componente central dessa arquitetura é a atenção: para calcular a representação de cada posição, o modelo combina informações de diferentes partes da sequência. Dessa forma, ao interpretar uma pergunta, pode relacionar um pronome ou uma referência a algo mencionado anteriormente no contexto.

O modelo aplica sucessivas camadas de operações matemáticas aos vetores de entrada. Em termos simplificados, cada camada refina as representações, integrando relações entre os tokens. Ao final, o modelo produz valores que indicam a compatibilidade de diferentess tokens candidatos para a próxima posição. Esses valores, chamados *logits*, são convertidos em uma distribuição de probabilidades.

O modelo não “procura” necessariamente uma resposta pronta em uma base de dados durante esse processo. Ele calcula uma continuação provável segundo os padrões que aprendeu e as informações presentes no contexto recebido. Sistemas podem combinar o modelo com busca, bases de conhecimento ou ferramentas externas, mas esses componentes são integrações adicionais, e não a própria inferência do LLM.

## 4. Geração autoregressiva: uma continuação de cada vez

Em uma geração autoregressiva, o modelo prevê o próximo token considerando os tokens anteriores. O sistema seleciona um token entre os candidatos e o acrescenta à sequência; em seguida, calcula o próximo, agora incluindo o token que acabou de gerar. Repetindo esse ciclo, constrói a resposta até atingir uma condição de parada, como um token de fim, um limite de tamanho ou uma regra definida pela aplicação.

Por isso, a resposta normalmente não é produzida de uma só vez. Mesmo que o serviço apresente o texto como uma mensagem contínua, os tokens podem ser calculados e enviados progressivamente. Essa característica permite que a pessoa comece a ler antes de a geração terminar, mas também significa que a geração depende de vários passos sucessivos: para produzir os tokens seguintes, o sistema precisa considerar os anteriores.

A seleção do próximo token envolve uma estratégia de **decodificação**. Uma escolha determinística, como selecionar sempre o candidato de maior probabilidade, tende a ser previsível, mas pode produzir respostas repetitivas. Estratégias probabilísticas permitem variar a saída. Parâmetros como temperatura modificam a distribuição usada na seleção: valores mais baixos tendem a concentrar as escolhas nos candidatos mais prováveis e valores mais altos permitem maior diversidade. O efeito concreto depende do modelo e dos demais parâmetros e não garante, por si só, mais criatividade ou maior correção.

Outras regras podem restringir candidatos ou limitar o formato da resposta. Por exemplo, uma aplicação pode pedir uma saída estruturada ou impedir a geração após determinado número de tokens. Esses controles orientam a geração, mas não transformam automaticamente o texto em informação verdadeira, a saída ainda precisa ser avaliada quanto a precisão e a adequação ao pedido.

## 5. Do pedido à resposta: GPUs, batching e duas fases

Depois da tokenização, o motor de inferência encaminha a solicitação para os recursos computacionais disponíveis com frequência, GPUs e agenda seu processamento. Como várias pessoas podem enviar pedidos ao mesmo tempo, o motor tenta usar o hardware de forma eficiente sem deixar cada solicitação esperando desnecessariamente.

Uma técnica importante é o **batching contínuo** (*continuous batching*). Em vez de formar um lote fixo e esperar que todas as solicitações terminem juntas, o motor pode inserir novas solicitações conforme há espaço e retirar as que já concluíram. Isso permite compartilhar o processamento do acelerador entre pedidos com diferentes comprimentos e tempos de geração. A técnica busca melhorar a utilização do hardware e a vazão, embora sua eficácia dependa da implementação e da carga.

O processamento de uma solicitação tem duas fases distintas:

1. **Prefill (pré-preenchimento):** o modelo lê os tokens do prompt e calcula as representações necessárias para iniciar a geração. Essa fase processa o contexto de entrada e constrói o cache KV. Em geral, é descrita como limitada pela computação (*compute-bound*), pois envolve operações intensivas sobre os tokens do prompt.
2. **Decode (decodificação):** depois do prefill, o modelo gera a resposta token por token. A cada passo, usa o contexto e o cache para calcular o token seguinte. Essa etapa é frequentemente limitada pela largura de banda da memória (*memory-bandwidth-bound*), porque é necessário movimentar os pesos e os dados relevantes na memória para cada novo token.

Essa distinção ajuda a entender por que um prompt muito longo pode aumentar o tempo antes do início da resposta, enquanto a geração de uma resposta extensa prolonga o tempo até sua conclusão. São partes diferentes do fluxo e podem pressionar recursos diferentes.

## 6. KV cache e eficiência durante a geração

Para evitar repetir certos cálculos a cada novo token, implementações de Transformers armazenam resultados intermediários de atenção em um **cache de chaves e valores**, conhecido como *KV cache*. Durante o prefill, o cache é construído para os tokens do prompt e durante o decode, é consultado e atualizado à medida que novos tokens são gerados. Reutilizar esses valores evita recalcular toda a sequência do início a cada passo. Isso torna a geração mais eficiente, embora o cache ocupe memória e cresça com o tamanho do contexto e da saída.

O cache não deve ser confundido com memória permanente do assistente. Ele é uma otimização computacional associada ao processamento da sequência em uma execução. A retenção de informações entre conversas, quando existe, é uma funcionalidade separada da aplicação e depende de como o serviço foi projetado.

Na prática, o atendimento pode envolver outros passos: montar as instruções, validar a solicitação, encaminhá-la a um modelo, filtrar ou formatar a resposta e devolvê-la pela interface. Assim, a experiência percebida pela pessoa depende tanto do modelo quanto do motor de inferência, da infraestrutura e do software que o envolve.

## 7. Desempenho: latência, vazão, memória e custo

Executar inferência exige computação e memória. Os parâmetros do modelo precisam estar disponíveis para os cálculos, e os vetores intermediários e o cache também consomem recursos. Aceleradores como GPUs são frequentemente usados porque executam operações paralelas de matrizes com eficiência, embora o hardware apropriado dependa do tamanho do modelo, da carga de trabalho e dos requisitos do serviço.

O vídeo destaca duas métricas de latência que ajudam a separar a espera inicial do ritmo de geração:

- **TTFT (*Time To First Token*):** tempo desde o envio do pedido até a chegada do primeiro token gerado. Inclui o processamento necessário para começar a resposta, especialmente o prefill, além de etapas de serviço e comunicação.
- **ITL (*Inter-Token Latency*):** intervalo de latência entre tokens sucessivos durante a geração. Ele indica o ritmo com que a resposta continua sendo produzida após o primeiro token.
- **Vazão (*throughput*):** quantidade de solicitações ou tokens que o sistema consegue processar em determinado intervalo.

TTFT e ITL ajudam a localizar diferentes aspectos da experiência: uma aplicação pode começar a responder rapidamente, mas depois gerar tokens lentamente ou pode levar mais tempo no início e então transmitir a resposta com rapidez. Por isso, uma única medida de “latência total” não descreve completamente a percepção de interatividade.

O tamanho do modelo, o comprimento do prompt e a quantidade de tokens gerados podem alterar o uso de memória, a latência e o custo. Técnicas de otimização, como quantização dos pesos, podem reduzir a memória necessária e acelerar a execução em alguns cenários, mas seus efeitos dependem do método, do hardware e da tarefa, podendo afetar a qualidade. Portanto, otimizar inferência envolve equilibrar velocidade, custo, vazão, uso de memória e experiência de cada pessoa; não há uma configuração única que maximize todos esses fatores ao mesmo tempo.

## 8. O que a inferência não garante

Uma resposta fluente não é prova de que o conteúdo está correto. O modelo estima continuações a partir de padrões e contexto; pode produzir erros, omitir ressalvas ou afirmar algo sem sustentação suficiente. O prompt pode orientar a tarefa, mas não elimina essas limitações. Em usos importantes, a saída deve ser verificada e, quando apropriado, apoiada por fontes confiáveis, ferramentas externas ou revisão humana.

Também é importante separar a capacidade do modelo da aplicação. Uma resposta pode depender de instruções do sistema, do histórico incluído, de documentos recuperados, de filtros e de parâmetros de geração. Ao avaliar um assistente, convém considerar todo esse fluxo e não atribuir cada comportamento exclusivamente ao modelo.

## Conclusão

Inferência é o mecanismo que transforma os pesos de um modelo treinado em respostas em tempo real. O motor de inferência recebe o pedido, tokeniza o texto, encaminha o trabalho ao hardware e coordena as solicitações. No prefill, processa o prompt e constrói o cache KV. No decode, gera a resposta token por token usando esse cache. O batching contínuo ajuda a compartilhar os recursos entre solicitações, enquanto TTFT e ITL medem aspectos distintos da latência.

Entender esse ciclo ajuda a explicar por que o tamanho do contexto, o comprimento da resposta, o hardware e a organização do serviço afetam custo e velocidade. A geração continua sendo uma previsão condicionada ao contexto, e não uma garantia automática de compreensão ou veracidade.

## Referências

- Vídeo da atividade: [What is LLM Inference? How AI Models Generate Response](https://www.youtube.com/watch?v=615-yWyS1n0).
- IBM Think: [What is LLM inference?](https://www.ibm.com/think/topics/llm-inference).
- Hugging Face, documentação sobre geração: [Generation strategies](https://huggingface.co/docs/transformers/generation_strategies).
