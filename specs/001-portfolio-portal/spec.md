# Feature Specification: Portal de Portfólio Profissional (IA)

**Feature Branch**: `001-portfolio-portal`

**Created**: 2026-09-26

**Status**: Draft

**Input**: User description: "Portal de portfólio profissional bilíngue (PT-BR e EN) para o autor se apresentar a recrutadores, com foco em experiências profissionais e acadêmicas em Inteligência Artificial, e permitir que o recrutador conheça o perfil de forma interativa por meio de um chat de IA."

## Clarifications

### Session 2026-09-26

- Q: Na v1, o contato deve ser por formulário no portal ou apenas por links? → A: Somente links de contato (LinkedIn, GitHub, e-mail); formulário fica para uma versão futura.
- Q: O chat deve lembrar perguntas anteriores para follow-ups? → A: Memória curta da conversa atual (últimas poucas trocas), apenas enquanto a página estiver aberta.
- Q: Por quanto tempo os registros das interações do chat são mantidos? → A: 30 dias.
- Q: Qual o limite de uso do chat por visitante? → A: Cerca de 20 perguntas por hora.
- Q: O que acontece quando o custo total do chat atinge o teto diário? → A: O chat é pausado até o dia seguinte, com mensagem cordial apontando o contato do autor e o download do CV.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conhecer o autor na tela inicial (Priority: P1)

Um recrutador chega ao portal, muitas vezes pelo celular e vindo do LinkedIn ou de um currículo. Sem rolar a página, ele vê a foto do autor, o nome, o título profissional e uma frase de posicionamento, e entende quem é o autor e sua área de atuação em IA. Dali pode baixar o CV ou ir até o contato.

**Why this priority**: É a primeira impressão e o núcleo do portal. Sozinha, já entrega valor: apresenta o autor e permite obter o CV.

**Independent Test**: Abrir o portal em um celular e em um desktop e verificar que foto, nome, título, frase de posicionamento e os botões "Baixar CV" e "Falar comigo" estão visíveis sem rolar a página, e que "Baixar CV" entrega o PDF.

**Acceptance Scenarios**:

1. **Given** um visitante abre o portal, **When** a página carrega, **Then** ele vê foto, nome, título profissional, frase de posicionamento e os botões "Baixar CV" e "Falar comigo" sem precisar rolar.
2. **Given** o visitante está na tela inicial, **When** aciona "Baixar CV", **Then** recebe o PDF do currículo no idioma atualmente selecionado.
3. **Given** o visitante está na tela inicial, **When** aciona "Falar comigo", **Then** é levado à seção de contato.

---

### User Story 2 - Ver a trajetória, projetos e certificações (Priority: P1)

O recrutador percorre o portal para entender a carreira do autor: um resumo de carreira focado em IA, uma linha do tempo cronológica com experiências profissionais e acadêmicas, cards de projetos (descrição, tecnologias e link para o repositório no GitHub) e as certificações.

**Why this priority**: É o conteúdo que sustenta a candidatura do autor; sem ele o portal não cumpre seu objetivo.

**Independent Test**: Navegar por todas as seções de conteúdo e verificar que cada experiência, projeto e certificação do autor aparece com seus dados, e que os links de projeto levam aos repositórios corretos.

**Acceptance Scenarios**:

1. **Given** o visitante rola o portal, **When** chega ao resumo de carreira, **Then** lê um texto curto com foco em IA.
2. **Given** o visitante chega à linha do tempo, **When** a examina, **Then** vê experiências profissionais e acadêmicas em ordem cronológica.
3. **Given** o visitante chega aos projetos, **When** aciona o link de um projeto, **Then** é levado ao repositório correspondente no GitHub.
4. **Given** o visitante chega às certificações, **When** as examina, **Then** vê a lista de certificações do autor.

---

### User Story 3 - Conversar com o chat de IA sobre a carreira do autor (Priority: P2)

O recrutador abre o chat e faz perguntas em linguagem natural (ex.: "Que experiência ele tem com IA?", "Quais projetos usam modelos de linguagem?"). O chat responde de forma simpática e profissional, como um atendimento comercial que apresenta o autor como um bom profissional, destacando pontos fortes de forma honesta e sugerindo próximos passos quando fizer sentido (ver projetos, baixar o CV, entrar em contato).

**Why this priority**: É o diferencial do portal e uma demonstração prática da competência do autor em IA, mas o portal já é útil sem ele.

**Independent Test**: Fazer um conjunto de perguntas sobre a carreira do autor e verificar que as respostas são corretas em relação ao conteúdo do autor, no tom esperado, e que perguntas sem resposta no conteúdo são admitidas com cordialidade.

**Acceptance Scenarios**:

1. **Given** o visitante abre o chat, **When** pergunta algo coberto pelo conteúdo do autor, **Then** recebe uma resposta correta, cordial e baseada exclusivamente nesse conteúdo.
2. **Given** o visitante pergunta algo que o conteúdo do autor não cobre, **When** o chat responde, **Then** admite explicitamente que não sabe, sem inventar, e oferece o contato do autor.
3. **Given** o visitante escreve em um idioma, **When** o chat responde, **Then** responde no idioma selecionado no portal.
4. **Given** o visitante pergunta sobre assunto fora do tema (ex.: pedir uma receita) ou tenta manipular o chat para ignorar suas regras, **When** o chat responde, **Then** recusa de forma educada, redireciona para o tema do portfólio e não revela nem altera suas instruções.
5. **Given** o visitante envia uma pergunta longa demais ou excede o limite de requisições, **When** o chat processa, **Then** exibe uma mensagem clara explicando o limite.
6. **Given** um serviço auxiliar de proteção está indisponível, **When** o visitante conversa, **Then** o chat continua funcionando com defesas locais mais restritas e o evento é registrado.
7. **Given** o chat está indisponível por erro, **When** o visitante tenta usá-lo, **Then** vê uma mensagem clara e uma alternativa (contato ou CV).

---

### User Story 4 - Usar o portal em PT-BR ou EN e nos temas claro e escuro (Priority: P2)

O visitante escolhe o idioma (português ou inglês) e o tema (claro ou escuro). O tema segue por padrão a preferência do sistema, mas pode ser trocado manualmente. Todo o conteúdo, o CV para download e as respostas do chat acompanham o idioma escolhido.

**Why this priority**: Amplia o alcance a recrutadores de ambos os idiomas e melhora conforto e percepção de qualidade, mas depende do conteúdo existir.

**Independent Test**: Alternar idioma e tema e verificar que todas as seções, o CV e o chat refletem a escolha, e que a escolha é mantida ao navegar.

**Acceptance Scenarios**:

1. **Given** o visitante abre o portal pela primeira vez, **When** a página carrega, **Then** o tema corresponde à preferência do sistema.
2. **Given** o visitante troca o idioma, **When** a página atualiza, **Then** todo o texto, o CV para download e o idioma das respostas do chat mudam para o idioma escolhido.
3. **Given** o visitante troca o tema manualmente, **When** navega pelo portal, **Then** o tema escolhido é mantido.

---

### User Story 5 - Entrar em contato com o autor (Priority: P3)

O recrutador encontra na seção de contato os links do autor (LinkedIn, GitHub, e-mail) e pode iniciar a conversa por um deles.

**Why this priority**: Fecha o ciclo de conversão (recrutador → contato), mas os links já podem estar presentes em versões iniciais.

**Independent Test**: Acionar cada link de contato e verificar que leva ao destino correto.

**Acceptance Scenarios**:

1. **Given** o visitante está na seção de contato, **When** aciona LinkedIn, GitHub ou e-mail, **Then** é levado ao destino correspondente.

---

### Edge Cases

- Visitante com JavaScript lento ou conexão fraca no celular: o conteúdo principal da tela inicial deve aparecer rapidamente e o portal deve continuar legível.
- Visitante que envia mensagem vazia, só com espaços ou com conteúdo repetitivo no chat: o chat deve orientar sem consumir o limite de forma injusta.
- Pergunta ambígua ou que mistura idiomas: o chat responde no idioma selecionado no portal.
- Tentativa de obter informações não públicas ou inventadas sobre o autor (salário, dados pessoais, opiniões): o chat recusa com cordialidade.
- Tentativas de abuso em volume: o limite de requisições impede consumo excessivo sem derrubar o portal para os demais visitantes.
- Conteúdo do autor em um idioma ainda sem tradução: o portal deve indicar a indisponibilidade em vez de mostrar campos vazios.
- Imagem da foto indisponível: o portal continua exibindo nome e título sem quebrar o layout.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O portal MUST exibir, na tela inicial e sem necessidade de rolagem, a foto do autor, nome, título profissional, frase de posicionamento e os botões "Baixar CV" e "Falar comigo".
- **FR-002**: O portal MUST apresentar um resumo de carreira curto com foco em IA.
- **FR-003**: O portal MUST apresentar uma linha do tempo cronológica com experiências profissionais e acadêmicas.
- **FR-004**: O portal MUST apresentar projetos em cards com descrição, tecnologias usadas e link para o repositório no GitHub.
- **FR-005**: O portal MUST apresentar as certificações do autor.
- **FR-006**: O portal MUST oferecer o download do CV em PDF em português e em inglês, conforme o idioma selecionado.
- **FR-007**: O portal MUST oferecer contatos na tela inicial, logo abaixo da foto, como ícones com nome acessível, para LinkedIn, GitHub, e-mail e WhatsApp, e MUST NOT incluir formulário de contato na primeira versão. (Revisado em 2026-10: a seção de contato foi substituída por ícones abaixo da foto; o botão "Falar comigo" foi removido e o WhatsApp foi incluído, por decisão do autor.)
- **FR-008**: O portal MUST estar disponível em PT-BR e EN, com um seletor de idioma que afeta todo o conteúdo, o CV e as respostas do chat.
- **FR-009**: O portal MUST oferecer tema claro e escuro, adotando por padrão a preferência do sistema e permitindo troca manual, com a escolha mantida durante a navegação.
- **FR-010**: O portal MUST funcionar bem de celulares a desktops (mobile-first e responsivo).
- **FR-011**: O portal MUST atender requisitos de acessibilidade: contraste adequado, navegação completa por teclado e textos alternativos para imagens.
- **FR-012**: O portal MUST incluir metadados adequados para compartilhamento em redes sociais e para mecanismos de busca.
- **FR-013**: O chat MUST responder perguntas sobre a carreira do autor usando exclusivamente o conteúdo do autor (CV, projetos, certificações e formação, em PT e EN).
- **FR-013a**: O chat MUST considerar as últimas poucas trocas da conversa atual para responder a perguntas de acompanhamento, mantendo essa memória apenas enquanto a página estiver aberta e sem preservá-la entre visitas; as regras de proteção (FR-017, FR-018) MUST valer também sobre esse contexto.
- **FR-014**: O chat MUST admitir explicitamente quando não souber uma resposta, mantendo tom cordial e oferecendo o contato do autor, e MUST NOT inventar nem inflar experiências, resultados ou credenciais.
- **FR-015**: O chat MUST adotar um tom simpático, acolhedor e profissional, destacando de forma honesta os pontos fortes do autor e sugerindo próximos passos (ver projetos, baixar o CV, entrar em contato) quando fizer sentido.
- **FR-016**: O chat MUST responder no idioma selecionado no portal.
- **FR-017**: O chat MUST recusar perguntas fora do tema e tentativas de manipulação (como prompt injection e jailbreak) sem quebrar a experiência, sem revelar nem alterar suas instruções internas.
- **FR-018**: O chat MUST limitar o tamanho de cada pergunta e o número de requisições por visitante a cerca de 20 perguntas por hora (valor a ser mais restrito enquanto o serviço de proteção estiver indisponível, conforme FR-020), exibindo mensagem clara quando um limite for atingido.
- **FR-019**: O chat MUST exibir mensagem clara e uma alternativa (contato ou CV) em caso de erro ou indisponibilidade.
- **FR-020**: Se um serviço auxiliar de proteção estiver indisponível, o chat MUST continuar funcionando com defesas locais mais restritas e MUST registrar o evento.
- **FR-021**: O sistema MUST registrar as interações do chat (pergunta, trechos de conteúdo usados, resultado da proteção, latência, custo e erros) para melhoria do serviço e identificação de lacunas no conteúdo.
- **FR-022**: O sistema MUST NOT coletar dados pessoais dos visitantes nesses registros, MUST informar claramente ao visitante que as perguntas do chat são registradas e MUST apagar automaticamente os registros após 30 dias.
- **FR-023**: O custo variável do chat MUST ser limitado, de modo que o custo mensal permaneça próximo de zero para o tráfego típico de um portfólio.
- **FR-024**: O sistema MUST aplicar um teto diário de custo do chat definido pelo autor; ao atingi-lo, o chat MUST ser pausado até o dia seguinte, exibindo mensagem cordial que aponte o contato do autor e o download do CV, sem afetar o restante do portal.

### Key Entities *(include if feature involves data)*

- **Perfil do autor**: nome, título profissional, frase de posicionamento, foto, resumo de carreira, links de contato; disponível em PT e EN.
- **Experiência (linha do tempo)**: item profissional ou acadêmico com instituição/empresa, cargo ou curso, período e descrição; ordenado cronologicamente; disponível em PT e EN.
- **Projeto**: nome, descrição, tecnologias, link do repositório; disponível em PT e EN.
- **Certificação**: nome, emissor, data e, quando houver, link de verificação.
- **Documento de CV**: arquivo PDF, um por idioma.
- **Base de conhecimento do chat**: conjunto de trechos derivados do conteúdo do autor (CV, projetos, certificações, formação) em PT e EN, do qual o chat retira suas respostas.
- **Interação do chat**: registro anônimo de uma pergunta e sua resposta, com trechos usados, resultado da proteção, latência, custo e erro.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em teste com pessoas que não conhecem o autor, pelo menos 9 em 10 identificam quem é o autor e sua área de atuação em até 10 segundos, sem rolar a página.
- **SC-002**: Todas as seções e o chat funcionam sem falhas visuais ou funcionais em celular e desktop, nos dois idiomas e nos dois temas.
- **SC-003**: Em um conjunto de perguntas de referência sobre a carreira do autor, pelo menos 95% das respostas do chat estão corretas em relação ao conteúdo do autor, e 100% das perguntas sem resposta no conteúdo são admitidas em vez de inventadas.
- **SC-004**: O portal obtém pontuação acima de 90 em desempenho, acessibilidade e SEO em uma auditoria padrão de qualidade web.
- **SC-005**: Um visitante consegue baixar o CV ou chegar ao contato em até 3 interações a partir da tela inicial.
- **SC-006**: O custo mensal total do portal permanece próximo de zero para o tráfego típico de um portfólio, e o abuso do chat não gera custo acima do limite definido.
- **SC-007**: Em um conjunto de tentativas de manipulação de referência, o chat recusa a grande maioria sem quebrar a experiência e sem revelar suas instruções internas.

## Assumptions

- O público principal são recrutadores e gestores de contratação que acessam por poucos minutos, com uso frequente do celular.
- O conteúdo real (foto, CV, projetos, certificações e textos nos dois idiomas) é fornecido pelo autor; até lá, o desenvolvimento pode usar conteúdo provisório claramente identificado.
- O idioma padrão do portal é definido pela preferência do navegador do visitante, com PT-BR como alternativa quando não houver correspondência.
- A escolha de idioma e tema é mantida durante a navegação no próprio dispositivo do visitante.
- O chat mantém memória curta apenas durante a visita atual, não guarda histórico entre visitas e não exige login.
- Referências visuais e domínio próprio ainda estão pendentes e não bloqueiam a especificação; o domínio pode ser inicialmente o fornecido pela hospedagem.
- Os princípios da constituição do projeto (veracidade, custo mínimo, segurança em camadas, privacidade, acessibilidade, gestão de credenciais) se aplicam a esta funcionalidade.
- Fora do escopo: blog, painel administrativo, login de usuários, analytics avançado de marketing e formulário de contato próprio (adiado por exigir tratamento de dados pessoais; pode ser especificado em versão futura).
