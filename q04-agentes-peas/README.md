# q04-agentes-peas

## O que é

Exercício de classificação de agentes inteligentes usando PEAS e propriedades dos ambientes de tarefa. São analisadas dez aplicações: dez aplicações listadas abaixo.

## Como rodar

Não tem código executável. O conteúdo é um relatório conceitual.

## Decisões tomadas (e por quê)

As propriedades descrevem o ambiente da aplicação, não apenas o software. Quando uma aplicação pode ser implementada de formas diferentes, a classificação abaixo explicita o escopo adotado. Em especial, um ambiente pode ser estocástico e ainda ser conhecido quando suas regras gerais são conhecidas, mas seus resultados não são previsíveis com certeza.

## Aplicações

### 1.1 Termostato - agente reativo simples

**PEAS**

| Elemento | Descrição |
|---|---|
| Performance | Manter a temperatura perto do alvo e diminuir o consumo de energia |
| Environment | Ambinates do espaço com temperatura variável |
| Actuators | Interruptor que liga ou desliga o aquecedor ou o ar-condicionado |
| Sensors | Sensor de temperatura |

**Propriedades do ambiente**

| Propriedade | Classificação | Justificativa |
|---|---|---|
| Observabilidade | Parcialmente observável | O sensor mede a temperatura apenas em seu ponto de instalação. |
| Determinismo | Estocástico | Portas abertas, clima externo e pessoas alteram a temperatura de formas difíceis de prever. |
| Episódico/Sequencial | Sequencial | A ação atual afeta a temperatura futura. |
| Estático/Dinâmico | Dinâmico | A temperatura muda mesmo sem ação do agente. |
| Discreto/Contínuo | Contínuo | Temperatura e tempo variam continuamente. |
| Nº de agentes | Agente único | O termostato é o único agente decisório considerado. |
| Conhecido/Desconhecido | Conhecido | As regras gerais do sistema, como o efeito de ligar o aquecedor, são conhecidas. |

**Por que é reativo simples:** escolhe a ação com base apenas na percepção atual.

**Por que não é baseado em modelo:** não mantém uma representação do estado do ambiente nem usa algum histórico para estimar sua evolução.

### 1.2 Filtro de spam por palavras-chave - agente reativo simples

**PEAS**

| Elemento | Descrição |
|---|---|
| Performance | Identificar spam e diminui tanto mensagens indesejadas na caixa de entrada quanto mensagens verdadeiras bloqueadas |
| Environment | Mensagens recebidas, caixa de entrada e regras de filtragem |
| Actuators | Marcar como spam, mover para a pasta de spam ou permitir a entrega |
| Sensors | Texto, remetente, assunto e outros campos da mensagem |

**Propriedades do ambiente**

| Propriedade | Classificação | Justificativa |
|---|---|---|
| Observabilidade | Parcialmente observável | O conteúdo não revela com certeza a intenção do remetente. |
| Determinismo | Estocástico | Palavras ambíguas e mudanças nas mensagens tornam incerta a classificação correta. |
| Episódico/Sequencial | Episódico | Cada mensagem pode ser classificada independentemente, sem depender das decisões anteriores. |
| Estático/Dinâmico | Estático durante a decisão | A mensagem não muda enquanto está sendo classificada, ou seja, o conjunto de mensagens muda com o tempo. |
| Discreto/Contínuo | Discreto | A ação é uma escolha entre categorias, como spam ou verdadeira. |
| Nº de agentes | Agente único | Considera-se apenas o filtro como agente decisório, remetentes fazem parte do ambiente. |
| Conhecido/Desconhecido | Conhecido | As palavras e regras usadas pelo filtro são definidas previamente. |

**Por que é reativo simples:** aplica regras diretamente aos atributos da mensagem atual.

**Por que não é baseado em modelo:** não conserva um modelo do remetente ou do histórico para deduzir estados não observados.

### 1.3 Aspirador robô com mapa - agente baseado em modelo

**PEAS**

| Elemento | Descrição |
|---|---|
| Performance | Limpar a maior área possível, evitar batidas e obstáculos e economizar bateria |
| Environment | Cômodos, sujeira, móveis, paredes, pessoas e estação de recarga |
| Actuators | Rodas, escovas, sucção e mecanismo de retorno para a base |
| Sensors | Sensores de distância, colisão, sujeira, posição e nível de bateria |

**Propriedades do ambiente**

| Propriedade | Classificação | Justificativa |
|---|---|---|
| Observabilidade | Parcialmente observável | Sensores têm alcance limitado e não detectam todos os obstáculos ou a sujeira. |
| Determinismo | Estocástico | Rodas podem derrapar e obstáculos ou pessoas podem alterar o percurso. |
| Episódico/Sequencial | Sequencial | Cada movimento afeta a posição e as opções de limpeza seguintes. |
| Estático/Dinâmico | Dinâmico | Pessoas e objetos podem se mover enquanto o robô trabalha. |
| Discreto/Contínuo | Contínuo | Posição e movimento são físicos e contínuos, embora o mapa possa ser discretizado em células. |
| Nº de agentes | Agente único | Há um robô decisório; pessoas são consideradas parte do ambiente. |
| Conhecido/Desconhecido | Conhecido | O mapa e as regras de movimento são conhecidos, ainda que haja ruído nas medições e ações. |

**Por que é baseado em modelo:** mantém um mapa e um estado interno, atualizados pelas noçoes do espaço, para inferir áreas já visitadas e obstáculos.

**Por que não é baseado em objetivo:** neste exemplo, a característica central é atualizar o modelo do ambiente, não foi especificada uma busca explícita por uma meta de destino.

### 1.4 Monitor de paciente em UTI - agente baseado em modelo

**PEAS**

| Elemento | Descrição |
|---|---|
| Performance | Detectar deterioração com rapidez, reduzir alarmes falsos e fornecer informação útil a equipe clínica |
| Environment | Paciente, leito, equipamentos e equipe de saúde |
| Actuators | Exibir sinais, emitir alarmes e notificar a equipe |
| Sensors | Sinais vitais, como frequência cardíaca, pressão arterial, saturação e temperatura |

**Propriedades do ambiente**

| Propriedade | Classificação | Justificativa |
|---|---|---|
| Observabilidade | Parcialmente observável | Os sinais medidos não revelam todas as condições clínicas do paciente. |
| Determinismo | Estocástico | A evolução clínica e a resposta a eventos não são totalmente previsíveis. |
| Episódico/Sequencial | Sequencial | Tendências ao longo do tempo são importantes para avaliar o estado do paciente. |
| Estático/Dinâmico | Dinâmico | Os sinais vitais podem mudar continuamente. |
| Discreto/Contínuo | Contínuo | A maioria dos sinais monitorados varia de forma continua, mesmo que os alarmes sejam discretos. |
| Nº de agentes | Agente único | O monitor é o único agente artificial considerado, já paciente e equipe são atores do ambiente. |
| Conhecido/Desconhecido | Parcialmente conhecido | Os sinais e limites são especificados, mas a resposta clínica individual é incerta. |

**Por que é baseado em modelo:** usa o estado atual e o histórico de sinais para acompanhar tendências, em vez de reagir a uma leitura isolada.

**Por que não é baseado em objetivo:** no escopo descrito, o monitor acompanha e alerta, não planeja uma sequência de ações clínicas para atingir uma meta.

### 1.5 Roteador de entregas - agente baseado em objetivo

**PEAS**

| Elemento | Descrição |
|---|---|
| Performance | Entregar todos os pedidos, respeitar prazos, regras e reduzir distância ou tempo de percurso |
| Environment | Rede viária, veículos, entregas, endereços, trânsito e condições das vias |
| Actuators | Atribuir pedidos, definir ou atualizar rotas e enviar instruções aos entregadores |
| Sensors | Endereços, mapa, localização dos veículos, pedidos e informações de trânsito |

**Propriedades do ambiente**

| Propriedade | Classificação | Justificativa |
|---|---|---|
| Observabilidade | Parcialmente observável | Trânsito, incidentes e condições das vias podem não estar totalmente visíveis. |
| Determinismo | Estocástico | Trânsito, atrasos e imprevistos alteram os tempos de viagem. |
| Episódico/Sequencial | Sequencial | A escolha de uma rota afeta a ordem e o horário das entregas seguintes. |
| Estático/Dinâmico | Dinâmico | Trânsito e disponibilidade dos veículos mudam durante o planejamento. |
| Discreto/Contínuo | Híbrido | Vias e entregas podem ser tratadas como elementos discretos, enquanto posição e tempo são contínuos. |
| Nº de agentes | Multiagente | Motoristas e outros usuários das vias também tomam decisões que afetam o percurso. |
| Conhecido/Desconhecido | Parcialmente conhecido | O mapa é conhecido, mas os tempos e eventos futuros não são totalmente conhecidos. |

**Por que é baseado em objetivo:** procura uma sequência de rotas e atribuições que alcance a meta de concluir as entregas.

**Por que não é baseado em utilidade:** na versão descrita, a prioridade é satisfazer as metas e restrições.

### 1.6 Robô de armazém - agente baseado em objetivo

**PEAS**

| Elemento | Descrição |
|---|---|
| Performance | Buscar e transportar itens até os destinos corretos, evitando batidas e atrasos |
| Environment | Corredores, prateleiras, itens, estações, trabalhadores e outros robôs |
| Actuators | Rodas, garra ou plataforma de carga, luzes e sinais de comunicação |
| Sensors | Câmeras, sensores de distância, localização, leitura de etiquetas e sensores de carga |

**Propriedades do ambiente**

| Propriedade | Classificação | Justificativa |
|---|---|---|
| Observabilidade | Parcialmente observável | Cargas, trabalhadores ou obstáculos podem estar fora do campo dos sensores. |
| Determinismo | Estocástico | Desvios, falhas e movimentação de pessoas ou robôs alteram o resultado das ações. |
| Episódico/Sequencial | Sequencial | Cada deslocamento e coleta influencia as tarefas que ainda podem ser realizadas. |
| Estático/Dinâmico | Dinâmico | Trabalhadores, robôs e itens podem se mover durante a operação. |
| Discreto/Contínuo | Híbrido | Tarefas e posições no mapa podem ser discretas, mas movimento e tempo são contínuos. |
| Nº de agentes | Multiagente | Outros robôs e trabalhadores compartilham o espaço e afetam o planejamento. |
| Conhecido/Desconhecido | Parcialmente conhecido | O layout e as regras são conhecidos, mas eventos e ocupação futura não são certos. |

**Por que é baseado em objetivo:** planeja movimentos para alcançar destinos, coletar itens e completar tarefas atribuídas.

**Por que não é baseado em utilidade:** no escopo descrito, só é preciso cumprir a tarefa com segurança, não foi definida uma função que compare velocidade, consumo e outras coisas.

### 1.7 Assistente de planejamento acadêmico - agente baseado em utilidade - Projeto P3 2025.2

**PEAS**

| Elemento | Descrição |
|---|---|
| Performance | Propor um plano que respeite prazos, distribua a carga de estudo e considere as preferências do estudante |
| Environment | Disciplinas, tarefas, provas, calendário, disponibilidade e preferências do estudante |
| Actuators | Sugerir horários, reorganizar tarefas e apresentar avisos ou recomendações |
| Sensors | Calendário, prazos, tarefas informadas, disponibilidade e preferências fornecidas pelo estudante |

**Propriedades do ambiente**

| Propriedade | Classificação | Justificativa |
|---|---|---|
| Observabilidade | Parcialmente observável | O assistente não conhece automaticamente toda a carga, disposição ou imprevistos do estudante. |
| Determinismo | Estocástico | A duração das tarefas e a disponibilidade futura podem variar. |
| Episódico/Sequencial | Sequencial | O plano de hoje afeta o tempo disponível e o progresso dos próximos dias. |
| Estático/Dinâmico | Dinâmico | Prazos, tarefas e disponibilidade mudam ao longo do semestre. |
| Discreto/Contínuo | Híbrido | Tarefas são discretas, enquanto horários e durações são contínuos. |
| Nº de agentes | Agente único | Considera-se o assistente como agente e o estudante fornece informações e recebe recomendações. |
| Conhecido/Desconhecido | Parcialmente conhecido | Prazos informados são conhecidos, mas preferências e durações podem ser estimadas com incerteza. |

**Por que é baseado em utilidade:** compara planos possíveis por critérios graduais, como cumprimento de prazos, equilíbrio da carga e preferência por horários.

**Por que não é baseado em aprendizagem:** os critérios e preferências são informados ou configurados, não há atualização automática do modelo a partir dos resultados de planos anteriores.

### 1.8 Carro autônomo - agente baseado em utilidade

**PEAS**

| Elemento | Descrição |
|---|---|
| Performance | Transportar passageiros com segurança e cumprir regras, equilibrando tempo, conforto e eficiência |
| Environment | Ruas, sinalização, veículos, pedestres, ciclistas, passageiros e condições climáticas |
| Actuators | Direção, acelerador, freios, transmissão e sinalização |
| Sensors | Câmeras, radar, lidar, GPS, sensores do veículo e mapas |

**Propriedades do ambiente**

| Propriedade | Classificação | Justificativa |
|---|---|---|
| Observabilidade | Parcialmente observável | Sensores têm alcance e precisão limitados e podem não detectar todas as intenções dos outros usuários. |
| Determinismo | Estocástico | Ações de outros usuários e condições da via tornam os resultados incertos. |
| Episódico/Sequencial | Sequencial | Cada manobra condiciona as decisões e a segurança dos instantes seguintes. |
| Estático/Dinâmico | Dinâmico | Trânsito, pedestres e condições da via mudam continuamente. |
| Discreto/Contínuo | Contínuo | Posição, velocidade, direção e tempo variam continuamente. |
| Nº de agentes | Multiagente | Motoristas, pedestres e ciclistas também tomam decisões. |
| Conhecido/Desconhecido | Parcialmente conhecido | Regras de trânsito são conhecidas, mas o comportamento dos demais e certas condições são incertos. |

**Por que é baseado em utilidade:** avalia consequências e equilibra objetivos concorrentes, dando prioridade a segurança sem ignorar conforto e eficiência.

**Por que não é baseado em aprendizagem:** a classificação descreve a tomada de decisão por uma função de utilidade, o uso de aprendizado para percepção ou previsão pode existir, mas não é o aspecto que o define.

### 1.9 Filtro de spam que aprende (Naive Bayes) - agente com aprendizagem

**PEAS**

| Elemento | Descrição |
|---|---|
| Performance | Classificar spam com boa precisão e revocação e evitar bloquear mensagens verdadeiras |
| Environment | Mensagens recebidas, caixa de entrada, remetentes e rótulos fornecidos por usuários |
| Actuators | Classificar, mover ou marcar mensagens e atualizar o modelo após receber correções |
| Sensors | Texto, remetente, assunto, outros atributos da mensagem e correções dos usuários |

**Propriedades do ambiente**

| Propriedade | Classificação | Justificativa |
|---|---|---|
| Observabilidade | Parcialmente observável | O conteúdo e os rótulos disponíveis não revelam perfeitamente a intenção do remetente. |
| Determinismo | Estocástico | Mensagens semelhantes podem ter classes diferentes, e os padrões de spam variam. |
| Episódico/Sequencial | Sequencial ao longo da aprendizagem | A classificação de uma mensagem é independente, mas os exemplos rotulados alteram o modelo usado nas próximas. |
| Estático/Dinâmico | Dinâmico | Os padrões de mensagens e as estratégias de spam mudam com o tempo. |
| Discreto/Contínuo | Discreto | A saída principal é uma categoria, como spam ou legítima. |
| Nº de agentes | Agente único | O filtro é o agente decisório e os remetentes fazem parte do ambiente. |
| Conhecido/Desconhecido | Desconhecido inicialmente | As distribuições das classes não são conhecidas por completo e são estimadas a partir de exemplos. |

**Por que é com aprendizagem:** ajusta o modelo Naive Bayes com mensagens rotuladas e pode melhorar ou adaptar as classificações com novos exemplos.

**Por que não é apenas reativo simples:** não depende somente de regras fixas para a mensagem atual, mas mantém parâmetros aprendidos que mudam com a experiência.

### 1.10 Analista de risco de crédito que aprende - agente com aprendizagem

**PEAS**

| Elemento | Descrição |
|---|---|
| Performance | Estimar risco de inadimplência com boa calibração, reduzir perdas e acompanhar critérios de equidade e conformidade |
| Environment | Solicitações de crédito, clientes, histórico de pagamentos e condições econômicas |
| Actuators | Gerar uma pontuação ou recomendação para análise humana, registrar previsões e sinalizar casos para revisão |
| Sensors | Dados cadastrais e financeiros autorizados, histórico de crédito e resultados de pagamentos |

**Propriedades do ambiente**

| Propriedade | Classificação | Justificativa |
|---|---|---|
| Observabilidade | Parcialmente observável | Os dados disponíveis não capturam toda a situação financeira nem todos os fatores futuros de inadimplência. |
| Determinismo | Estocástico | O pagamento futuro depende de eventos econômicos e pessoais incertos. |
| Episódico/Sequencial | Sequencial | Resultados de empréstimos anteriores alimentam o aprendizado e afetam previsões futuras. |
| Estático/Dinâmico | Dinâmico | Perfil dos clientes e condições econômicas mudam ao longo do tempo. |
| Discreto/Contínuo | Híbrido | A decisão pode ser categórica ou uma faixa de risco, enquanto renda e pontuações são numéricas. |
| Nº de agentes | Agente único | Considera-se o sistema de análise como agente. Clientes e instituições fazem parte do ambiente. |
| Conhecido/Desconhecido | Desconhecido inicialmente | A relação entre os dados e os resultados é estimada e atualizada com observações históricas. |

**Por que é com aprendizagem:** aprende padrões a partir dos resultados observados e atualiza o modelo para estimar o risco de novos casos.

**Por que não é apenas baseado em modelo ou em utilidade:** um modelo do perfil atual ou uma função de custos não define esta aplicação. A característica central é aprender a relação entre os dados e os resultados. A recomendação deve apoiar a análise, com revisão e critérios de equidade apropriados.

## Resultados

Foram descritas as dez aplicações, com PEAS, propriedades do ambiente e justificativa da categoria do agente. As classificações dependem das premissas indicadas em cada exemplo.

## Status

- [x] Código/conteúdo
- [x] Relatório
- [ ] Demo/vídeo (atividade conceitual sem código)
