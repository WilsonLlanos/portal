# Feature Specification: Observabilidade do Chat com Trace Completo e Avaliação Automática

**Feature Branch**: `002-chat-observability`

**Created**: 2026-10-31

**Status**: Draft

**Input**: User description: "Observabilidade do chat com trace completo no Langfuse e avaliação automática por LLM-como-juiz para detectar lacunas no conteúdo do autor. Hoje cada pergunta gera um único evento com os números finais; o outcome 'no_answer' quase nunca acontece, porque a busca sempre devolve os 5 trechos mais parecidos e quem decide que não há resposta é o LLM, sem o pipeline saber. Queremos: trace completo por pergunta (guardrail, embedding, busca com notas, geração com modelo/tokens/custo/tempo até o primeiro token), a maior nota de similaridade como métrica, um juiz configurado no painel do Langfuse usando o Gemini por conexão própria, que marca se a resposta admitiu não ter a informação, amostragem configurável e chave do Gemini separada para o juiz. Restrições: sem dados pessoais (pergunta e histórico sanitizados), trace pode conter o system prompt e os trechos recuperados, chat não pode depender da observabilidade, caber no plano Hobby, custo do juiz em centavos por mês, passo a passo documentado no quickstart. Fora do escopo: reagir ao 'no_answer' em tempo real na interface, dashboards personalizados e alertas."

## Contexto

Esta funcionalidade complementa a feature [001-portfolio-portal](../001-portfolio-portal/spec.md), em especial FR-021 (registrar as interações do chat), FR-022 (privacidade dos registros) e o uso planejado de `outcome = no_answer` para identificar lacunas no conteúdo do autor ([data-model.md § 3](../001-portfolio-portal/data-model.md)).

Hoje o registro de cada pergunta é um resumo único com os números finais, sem o passo a passo. E a classificação "sem resposta" quase nunca é registrada: a busca sempre devolve os trechos mais parecidos, mesmo quando nenhum deles responde à pergunta, e quem percebe a falta de informação é o modelo de linguagem, ao redigir a resposta. O resultado é que o autor não consegue descobrir quais perguntas dos recrutadores o seu conteúdo não cobre.

O usuário desta funcionalidade é o **autor do portal**, que opera o chat e mantém o conteúdo. O visitante do portal não percebe nenhuma mudança.

## Clarifications

### Session 2026-10-31

- Q: Quando o chat recusa por conta própria uma pergunta fora do tema ou que pede informação privada, como o avaliador deve classificar a resposta? → A: Três categorias: "respondeu", "lacuna" (assunto do portfólio sem informação no conteúdo) e "recusa" (fora do tema ou informação privada). Só "lacuna" alimenta a lista de lacunas no conteúdo.
- Q: As perguntas de uma mesma conversa devem aparecer agrupadas no painel ou como registros soltos? → A: Agrupadas por conversa, com um identificador aleatório criado pelo navegador ao abrir o chat e descartado ao fechar ou recarregar a página; não é guardado e não identifica o visitante. Cada pergunta continua sendo um registro próprio, e a avaliação continua sendo por resposta.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inspecionar o passo a passo de uma pergunta (Priority: P1)

O autor abre o painel de observabilidade e escolhe uma pergunta feita por um visitante. Ele vê, em ordem, cada etapa pela qual a pergunta passou: a decisão do guardrail (e se ele estava normal ou degradado), a preparação da pergunta para a busca, os trechos recuperados com a nota de similaridade de cada um, e a geração da resposta (modelo usado, o que o modelo recebeu, o que respondeu, tokens, custo e quanto tempo levou até a primeira palavra). Com isso, entende por que o chat respondeu daquele jeito e onde o tempo foi gasto.

**Why this priority**: É a base de toda a observabilidade: sem o passo a passo, não há como depurar respostas ruins nem avaliar automaticamente as respostas (US2 depende desta).

**Independent Test**: Fazer uma pergunta coberta pelo conteúdo, uma recusada pelo guardrail e uma que exceda o limite por visitante, e verificar no painel que cada uma aparece com as etapas esperadas, o outcome correto e nenhum dado pessoal.

**Acceptance Scenarios**:

1. **Given** um visitante faz uma pergunta coberta pelo conteúdo, **When** o autor abre o registro dessa pergunta no painel, **Then** vê as etapas guardrail, preparação da busca, busca e geração, em ordem, com a duração de cada uma.
2. **Given** o registro de uma pergunta respondida, **When** o autor examina a etapa de busca, **Then** vê os identificadores dos trechos recuperados e a nota de similaridade de cada um.
3. **Given** o registro de uma pergunta respondida, **When** o autor examina a etapa de geração, **Then** vê o modelo usado, a entrada enviada ao modelo (instruções, trechos, histórico e pergunta), a resposta, os tokens de entrada e saída, o custo estimado e o tempo até o primeiro token.
4. **Given** uma pergunta recusada pelo guardrail, limitada por excesso de uso, feita com o chat pausado pelo teto de custo ou que terminou em erro, **When** o autor procura essa pergunta no painel, **Then** encontra um registro com o outcome correspondente e as etapas que chegaram a ser executadas.
5. **Given** um visitante digitou um e-mail ou um número de telefone na pergunta ou no histórico da conversa, **When** o autor abre o registro, **Then** esses dados aparecem substituídos por marcadores, inclusive quando a resposta do chat os repete, e não há IP, user agent nem identificador do visitante.
6. **Given** um visitante fez três perguntas seguidas na mesma conversa, **When** o autor abre essa conversa no painel, **Then** vê os três registros agrupados, em ordem cronológica, cada um clicável para ver as próprias etapas.

---

### User Story 2 - Descobrir lacunas no conteúdo por avaliação automática (Priority: P2)

Sem precisar ler conversa por conversa, o autor filtra no painel as perguntas marcadas como "lacuna": assuntos do portfólio que o conteúdo não cobre. Essa marcação é feita automaticamente, em segundo plano, por um modelo de linguagem avaliador que lê a pergunta e a resposta e registra um veredito com justificativa ("respondeu", "lacuna" ou "recusa"). Recusas de perguntas fora do tema ou de informação privada ficam separadas e não entram na lista. Com a lista, o autor decide o que acrescentar ao CV, aos projetos ou à descrição técnica do portal.

**Why this priority**: É o principal uso planejado da observabilidade (identificar lacunas no conteúdo) e hoje não funciona. Depende da US1, pois a avaliação opera sobre a pergunta e a resposta guardadas no registro da interação.

**Independent Test**: Fazer um conjunto de perguntas de referência com as três situações — cobertas pelo conteúdo, sobre o portfólio mas sem informação no conteúdo, e fora do tema ou privadas (ex.: salário, endereço) — e verificar no painel que a avaliação marcou cada resposta com a categoria correta ("respondeu", "lacuna" ou "recusa") e justificativa, sem alterar nem atrasar as respostas do chat.

**Acceptance Scenarios**:

1. **Given** o visitante perguntou sobre um assunto do portfólio (carreira, projetos, formação, o próprio portal) e o chat respondeu que não tem acesso a essa informação, **When** a avaliação automática roda, **Then** a resposta recebe a marcação "lacuna", com justificativa.
2. **Given** o chat respondeu com base no conteúdo do autor, **When** a avaliação automática roda, **Then** a resposta recebe a marcação "respondeu", com justificativa.
3. **Given** o visitante perguntou algo fora do tema (ex.: "qual a capital da França?") ou pediu informação privada (ex.: salário, endereço) e o chat recusou, **When** a avaliação automática roda, **Then** a resposta recebe a marcação "recusa", com justificativa, e não entra na lista de lacunas.
4. **Given** existem respostas avaliadas em um período, **When** o autor filtra por "lacuna", **Then** obtém a lista das perguntas correspondentes desse período.
5. **Given** o avaliador está indisponível ou falha, **When** um visitante conversa com o chat, **Then** o chat responde normalmente, no mesmo tempo, e a pergunta apenas fica sem avaliação.
6. **Given** a taxa de amostragem está configurada abaixo de 100%, **When** várias perguntas são feitas, **Then** apenas a fração configurada das respostas é avaliada.

---

### User Story 3 - Acompanhar custo, desempenho e saúde do chat (Priority: P3)

O autor acompanha, por período, o custo e o tempo de resposta do chat, a proporção de perguntas recusadas pelo guardrail e os períodos em que o guardrail operou degradado. Também compara a maior nota de similaridade da busca entre as respostas avaliadas como "respondeu" e como "lacuna", para saber se uma nota baixa indica com segurança falta de conteúdo.

**Why this priority**: Ajuda a calibrar o teto diário de custo e a qualidade da busca, mas o autor já consegue operar o chat sem isso.

**Independent Test**: Após um conjunto de perguntas, verificar no painel que é possível ver o custo total e a latência por período, filtrar por guardrail degradado e comparar a maior nota de similaridade entre respostas avaliadas como "respondeu" e "lacuna".

**Acceptance Scenarios**:

1. **Given** várias perguntas registradas em um dia, **When** o autor consulta o painel, **Then** vê o custo total e o tempo de resposta desse dia, agregados a partir das etapas de geração.
2. **Given** perguntas feitas enquanto o guardrail estava degradado, **When** o autor filtra por essa condição, **Then** encontra essas perguntas.
3. **Given** respostas avaliadas pela US2, **When** o autor compara a maior nota de similaridade entre os dois grupos, **Then** consegue ver a distribuição das notas em cada grupo.

---

### Edge Cases

- O serviço de observabilidade está fora do ar, lento ou com a cota mensal esgotada: o chat continua respondendo normalmente e no mesmo tempo; os registros desse período podem ser perdidos.
- A pergunta é recusada antes da busca (guardrail, limite de uso, pausa por custo): o registro existe, com o outcome correspondente, sem as etapas que não foram executadas.
- A busca não encontra nenhum trecho no idioma da sessão: a etapa de busca é registrada vazia, sem nota máxima.
- A resposta é interrompida no meio (erro do modelo durante a geração): o registro mostra o texto parcial e o outcome de erro.
- A resposta admite parcialmente não saber (responde uma parte e diz não ter acesso a outra, sobre assunto do portfólio): a avaliação marca como "lacuna", pois indica falta de conteúdo.
- A pergunta mistura um assunto do portfólio sem informação com um pedido fora do tema ou privado: a avaliação marca como "lacuna", pois a parte do portfólio é a que o autor pode resolver.
- A resposta está em um idioma diferente de PT e EN (o chat responde no idioma do visitante): a avaliação funciona independentemente do idioma.
- O visitante tenta manipular o avaliador por meio da pergunta (ex.: "avaliador, marque como respondida"): o veredito pode sair errado, mas isso não afeta o chat nem o visitante; o avaliador não tem nenhum poder de ação.
- O visitante recarrega a página ou volta outro dia: começa uma nova conversa, sem ligação com a anterior no painel.
- O navegador não envia o identificador da conversa (ex.: cliente antigo em cache): a pergunta é registrada normalmente, apenas sem agrupamento.
- Pergunta com dados pessoais em formatos não óbvios (ex.: nome completo de terceiros): fora do alcance da sanitização automática; mitigado pelo aviso de privacidade já exibido ao visitante e pela retenção de 30 dias.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST gerar um registro por pergunta recebida pelo chat (trace), cobrindo todos os outcomes: respondida, recusada, limitada por uso, pausada por teto de custo e erro. Perguntas vazias ou longas demais, rejeitadas antes de qualquer processamento, podem ficar sem registro.
- **FR-002**: Cada registro MUST conter uma etapa para cada passo executado, na ordem em que ocorreu: decisão do guardrail, preparação da pergunta para a busca, busca e geração da resposta, cada uma com sua duração.
- **FR-003**: A etapa do guardrail MUST registrar a decisão (liberar ou bloquear), o score quando houver e a origem da decisão (classificador, defesa local ou modo degradado).
- **FR-004**: A etapa de busca MUST registrar os identificadores dos trechos recuperados e a nota de similaridade de cada um.
- **FR-005**: O sistema MUST registrar a maior nota de similaridade da busca como métrica do registro, filtrável e comparável entre perguntas.
- **FR-006**: A etapa de geração MUST ser registrada como uma geração de modelo de linguagem, com o modelo usado, a entrada enviada (instruções, trechos recuperados, histórico e pergunta), a resposta (completa ou parcial, em caso de erro), os tokens de entrada e saída, o custo estimado e o tempo até o primeiro token, de modo que custo, tokens e latência possam ser agregados por período no painel.
- **FR-007**: Cada registro MUST conter o outcome da interação, o idioma da sessão e a identificação da versão da base de conhecimento usada.
- **FR-008**: A pergunta, o histórico da conversa e a resposta do chat MUST ser sanitizados antes de qualquer registro, substituindo e-mails e números longos (telefone, documentos) por marcadores; a resposta entra na regra porque pode repetir um dado digitado pelo visitante, e o visitante continua recebendo a resposta original. Os registros MUST NOT conter IP, user agent nem qualquer identificador do visitante; o identificador de conversa de FR-017 é permitido por não identificar o visitante.
- **FR-009**: O sistema MUST continuar respondendo ao visitante normalmente, sem aumento perceptível no tempo de resposta, quando o serviço de observabilidade estiver indisponível, lento ou com a cota esgotada. Falhas no registro MUST ser apenas anotadas no log da aplicação.
- **FR-010**: Uma avaliação automática MUST classificar cada resposta avaliada do chat em exatamente uma de três categorias, com uma justificativa, a partir da pergunta (sanitizada) e da resposta guardadas no registro da interação: "respondeu" (a resposta usou o conteúdo do autor), "lacuna" (a pergunta é sobre um assunto do portfólio — carreira, projetos, formação, certificações ou o próprio portal — e a resposta admitiu não ter a informação) ou "recusa" (a pergunta é fora do tema ou pede informação privada, e o chat recusou).
- **FR-011**: A avaliação automática MUST rodar em segundo plano, depois de a resposta ter sido entregue ao visitante, e MUST NOT alterar nem atrasar a resposta. Falhas da avaliação MUST NOT afetar o chat.
- **FR-012**: A avaliação automática MUST ser configurada no serviço de observabilidade, fora do código do chat, e MUST permitir definir a taxa de amostragem (fração das respostas avaliadas).
- **FR-013**: A avaliação automática MUST usar uma credencial de modelo de linguagem própria, separada da credencial usada pelo chat, com cota de uso própria.
- **FR-014**: A marcação "lacuna" MUST substituir o outcome "sem resposta" atual como fonte oficial das lacunas no conteúdo do autor; o autor MUST conseguir filtrar as perguntas assim marcadas em um período. Respostas marcadas como "recusa" MUST NOT entrar nessa lista.
- **FR-015**: O passo a passo para configurar a avaliação automática (credencial do avaliador, critério de avaliação, regra de execução e amostragem) e para consultar as lacunas no painel MUST estar documentado no guia de execução do projeto.
- **FR-016**: O volume de registros e avaliações MUST caber no plano gratuito do serviço de observabilidade no tráfego típico de um portfólio, e o custo mensal da avaliação automática MUST permanecer na casa dos centavos.
- **FR-017**: Os registros de uma mesma conversa MUST ser agrupados no painel por um identificador de conversa aleatório, gerado no navegador ao abrir o chat, mantido apenas enquanto a página estiver aberta e descartado ao fechar ou recarregar. Esse identificador MUST NOT ser persistido no navegador nem derivado de IP, user agent ou qualquer dado do visitante. Na ausência do identificador, a pergunta MUST ser registrada normalmente, sem agrupamento.

### Key Entities *(include if feature involves data)*

- **Registro da interação (trace)**: uma pergunta do visitante do início ao fim; tem outcome, idioma, versão da base de conhecimento, pergunta e resposta sanitizadas, maior nota de similaridade e as etapas executadas. Substitui o registro resumido atual (ChatInteraction da feature 001).
- **Etapa**: um passo do processamento (guardrail, preparação da busca, busca, geração), com duração, entrada e saída próprias.
- **Geração**: etapa especial que representa a chamada ao modelo de linguagem; tem modelo, entrada, resposta, tokens, custo e tempo até o primeiro token.
- **Avaliação**: veredito do avaliador automático sobre uma resposta do chat — "respondeu", "lacuna" ou "recusa" —, com justificativa; é a fonte das lacunas no conteúdo.
- **Conversa**: agrupamento dos registros feitos enquanto a página do chat esteve aberta, identificado por um valor aleatório e efêmero; não identifica o visitante nem liga visitas diferentes.
- **Lacuna no conteúdo**: pergunta cuja resposta foi avaliada como "lacuna"; insumo para o autor atualizar o conteúdo do portal. Recusas (fora do tema ou informação privada) não são lacunas.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das perguntas processadas (respondidas, recusadas, limitadas, pausadas ou com erro) geram um registro consultável no painel, quando o serviço de observabilidade está disponível.
- **SC-002**: Em uma auditoria de 50 registros com perguntas de teste contendo e-mails e telefones, nenhum registro contém esses dados nem IP, user agent ou identificador do visitante.
- **SC-003**: Com o serviço de observabilidade indisponível, o chat responde a 100% das perguntas, e o tempo até a primeira palavra da resposta não aumenta mais que 10% em relação ao funcionamento normal.
- **SC-004**: Em um conjunto de referência com pelo menos 21 perguntas (pelo menos 7 de cada categoria: "respondeu", "lacuna" e "recusa"), a avaliação automática classifica corretamente pelo menos 90% das respostas, e no máximo 1 resposta de "recusa" é classificada como "lacuna".
- **SC-005**: O autor obtém a lista das lacunas de um período (perguntas cujas respostas foram avaliadas como "lacuna") em menos de 2 minutos, a partir do painel, sem ler conversas individualmente.
- **SC-006**: Com até 1.000 perguntas por mês, o volume de registros e avaliações fica dentro do plano gratuito do serviço de observabilidade, e o custo da avaliação automática fica abaixo de US$ 0,50 por mês.
- **SC-007**: Para qualquer pergunta registrada, o autor identifica em menos de 1 minuto qual etapa consumiu mais tempo e quais trechos embasaram a resposta.

## Assumptions

- O serviço de observabilidade é o Langfuse Cloud, plano Hobby (50 mil unidades por mês, 30 dias de retenção, avaliações por LLM-como-juiz incluídas), já escolhido na feature 001 (research.md D7). A retenção de 30 dias continua atendendo FR-022 da feature 001.
- O avaliador usa o Gemini, por uma conexão de modelo configurada no próprio Langfuse, cobrada na conta Google do autor; a chave é exclusiva do avaliador, restrita e com cota (constituição, Princípio IX), criada num projeto do Google Cloud separado do chat, porque no Gemini a cota e os limites valem por projeto, não por chave.
- As regras de avaliação do Langfuse operam sobre observações e só enxergam os dados da observação avaliada; por isso a avaliação é aplicada à observação raiz da interação, que guarda exatamente a pergunta sanitizada e a resposta (a etapa de geração também contém as instruções e os trechos, o que aumentaria custo e ruído). Ver research.md R4.
- A taxa de amostragem começa em 100%, já que o tráfego de um portfólio é baixo; pode ser reduzida se o custo ou a cota exigirem.
- Registrar as instruções do chat (system prompt) e os trechos recuperados no painel é aceitável, pois o painel é privado e os trechos são conteúdo público do autor.
- O modo de registro atual (um evento resumido por pergunta) é substituído pelo registro completo; não é necessário manter os dois.
- O autor é o único usuário do painel (o plano permite até 2 usuários).
- O agrupamento por conversa exige que o frontend do chat envie o identificador de conversa junto com cada pergunta; é a única mudança visível no código do frontend, e não altera nada que o visitante veja.
- O outcome técnico "sem resposta" (busca vazia) pode continuar existindo para os casos de falha da busca, mas deixa de ser a fonte das lacunas no conteúdo.
- Fora do escopo: reagir à falta de resposta em tempo real na interface do chat (ex.: botão de contato), dashboards personalizados, alertas e avaliações além da classificação "respondeu"/"lacuna"/"recusa" (ex.: fidelidade da resposta aos trechos), que podem ser especificadas em uma versão futura.
