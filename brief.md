# Brief — Portal de Portfólio Profissional (IA)

## 1. Objetivo
Apresentar minha trajetória e meus projetos a recrutadores, com foco em experiências profissionais e acadêmicas em Inteligência Artificial. O portal deve causar boa primeira impressão em poucos segundos e permitir que o recrutador conheça meu perfil de forma interativa por meio de um chat com IA.

## 2. Público-alvo
- Recrutadores e gestores de contratação (técnicos e não técnicos), em vagas de IA/dados/engenharia.
- Uso típico: acesso rápido (1–3 min), muitas vezes pelo celular, vindo de LinkedIn ou de um currículo.

## 3. Conteúdo e seções
1. **Hero (tela inicial):** minha foto, nome, título profissional, frase de posicionamento, botões "Baixar CV" e "Falar comigo".
2. **Resumo de carreira:** texto curto com foco em IA.
3. **Linha do tempo:** experiências profissionais e acadêmicas, em ordem cronológica.
4. **Projetos:** cards com descrição, tecnologias usadas e link para o GitHub.
5. **Certificações.**
6. **Chat com IA (RAG):** o recrutador pergunta sobre minha carreira e recebe respostas baseadas nos meus documentos (CV, projetos, certificações).
7. **Contato:** links (LinkedIn, GitHub, e-mail) e/ou formulário.
8. **Download do CV** (PDF), disponível também nos dois idiomas.

## 4. Requisitos de experiência
- **Bilíngue:** português (PT-BR) e inglês, com seletor de idioma. O chat de IA responde no idioma escolhido.
- **Responsivo:** mobile-first, funcionando de celular a desktop.
- **Tema claro e escuro:** respeita a preferência do sistema e permite troca manual.
- **Visual moderno:** limpo, tipografia forte, animações sutis. Referências visuais: *a definir*.
- **Desempenho e SEO:** carregamento rápido, boas pontuações no Lighthouse, metadados para compartilhamento (Open Graph).
- **Acessibilidade:** contraste adequado, navegação por teclado, textos alternativos.

## 5. Chat com IA (RAG)
- Base de conhecimento: meu CV, descrições de projetos, certificações e formação (em PT e EN).
- Responde apenas com base nesses documentos e admite quando não sabe. Não inventa informações sobre mim.
- Proteções: limite de requisições por visitante (controle de custo) e mensagem clara de erro/indisponibilidade.
- Sem armazenar dados pessoais dos visitantes além do necessário.

## 5.1 Segurança do chat (guardrails) — a investigar
Objetivo: impedir prompt injection, jailbreak e uso indevido do chat (que é público e consome LLM pago), com custo zero ou mínimo. Cada candidato deve ser avaliado nos critérios: **custo, latência, tamanho/dependências (limite de funções serverless da Vercel), suporte a PT/EN, acurácia e facilidade de manutenção**.

Candidatos:
- **Llama Prompt Guard 2** (22M e 86M) — **escolha preferencial do autor**: classificador dedicado de prompt injection/jailbreak. Formas de implantação a comparar no plano: (a) API hospedada (ex.: Groq), (b) versão ONNX quantizada dentro da função da Vercel, (c) microsserviço separado gratuito (ex.: Hugging Face Space), mantendo o restante na Vercel. Verificar licença e acesso ao modelo (Hugging Face), cobertura de português (a variante 86M é a multilíngue), limite de contexto (~512 tokens, logo o input do chat deve ser limitado) e latência. O guardrail também fica atrás de uma interface (`InputGuard`) para permitir troca. Se for a opção (c): o Hugging Face Space hospeda **somente o classificador** (um endpoint `POST /classify` com FastAPI em Docker), protegido por segredo compartilhado; o backend principal segue na Vercel. **Política de falha definida (fail-open com degradação):** se o Space não responder dentro de um timeout curto, o chat segue normalmente aplicando apenas as defesas locais (limite de tamanho, heurísticas, rate limit mais restrito, system prompt endurecido), e o evento é registrado na observabilidade. Um circuit breaker simples evita esperar o timeout a cada pergunta enquanto o serviço estiver fora. Cold start mitigado com ping periódico ao endpoint `/health` do Space. **Escolha do autor: workflow agendado do GitHub Actions** (`on: schedule` com `cron`, executando um `curl` com falha explícita se a resposta não for 200), também como oportunidade de aprendizado de GitHub Actions. Pontos a validar no plano: intervalo do cron frente às regras de suspensão do Space; atrasos e imprecisão dos agendamentos do GitHub; desativação automática de workflows agendados após ~60 dias sem atividade no repositório (mitigar com commits periódicos ou reativação); e `workflow_dispatch` para disparo manual. Serviço gratuito de monitoramento (ex.: UptimeRobot) fica como complemento opcional para alertas.

## 5.4 CI/CD com GitHub Actions — a definir no plano
O autor quer aprender GitHub Actions com este projeto. Candidatos de workflows: (1) ping agendado do Space (item acima); (2) CI em pull requests com lint, testes e build do frontend (React/Next.js) e do backend (Python); (3) regeneração dos embeddings quando o conteúdo do CV/projetos mudar; (4) verificação periódica de saúde do portal em produção. Segredos (URL do Space, segredo compartilhado) guardados em *GitHub Secrets*, nunca no repositório.

Nota de escopo: o deploy do frontend/backend na Vercel é automático a cada push na `main`, então não haverá pipeline de deploy próprio para eles; o foco do aprendizado é CI e automação agendada (o CD se limita a bloquear merges com CI falhando e, opcionalmente, publicar o Space do Hugging Face via Actions). Manter os pipelines pequenos e proporcionais ao projeto.

Ordem sugerida de implementação (complexidade crescente):
1. **Ping agendado** do Space: `schedule` + `curl`, uso de Secrets e `workflow_dispatch`.
2. **CI do frontend:** `npm ci`, lint e build em cada pull request, com cache de dependências.
3. **CI do backend:** `uv sync`, `ruff` e `pytest`.
4. **Regeneração de embeddings:** gatilho por caminho (`paths:`) quando o conteúdo do CV/projetos mudar.
5. **Proteção da `main`:** exigir CI verde antes do merge.

## 5.3 Observabilidade — a definir no plano
Objetivo: entender o comportamento do chat e detectar problemas, de forma proporcional a um portfólio (custo zero).
- **Rastreamento do chat (RAG):** pergunta, trechos recuperados, resultado do guardrail, tokens, custo estimado, latência e erros. Candidato: Langfuse (código aberto, camada gratuita) ou equivalente; avaliar também simples logs estruturados (JSON).
- **Saúde:** endpoint `/health`, monitoramento de disponibilidade (backend e Space do guardrail) e alerta simples de falha.
- **Métricas úteis:** taxa de bloqueio do guardrail, perguntas sem resposta (lacunas no CV), fallback ativado, custo por dia.
- **Privacidade:** não registrar dados pessoais, definir retenção curta, e informar ao visitante que as perguntas do chat são registradas para melhoria do serviço.
- **Frontend:** analytics leve e sem cookies (ex.: Vercel Web Analytics) apenas se a camada gratuita permitir.
- **Guardrails AI** (framework de validadores): avaliar se agrega valor além de validadores próprios simples, considerando peso das dependências.
- **Classificador com LLM pequeno** (saída booleana `injection: true/false`) — apenas plano B, caso o Prompt Guard 2 se mostre inviável.
- **Jev (TypeSafe AI)**: modelo de decisões estruturadas/tipadas, sem conversa. *Descartado por ora*, por ser muito novo e sem informação verificada; pode ser reavaliado no futuro.
- **Defesas em camadas sem custo de modelo:** limite de tamanho do input, limite de requisições por visitante, heurísticas/regex, system prompt endurecido, resposta restrita ao contexto recuperado e verificação da saída.

Decisão esperada no plano: arquitetura de defesa em camadas, priorizando o que é gratuito e cabe na Vercel; classificadores pagos ou pesados só se justificarem.

## 5.2 Otimização de custo do LLM — a investigar
- **Prompt caching** do provedor escolhido: verificar se é aplicável. Pontos a checar: tamanho mínimo do prefixo para o cache funcionar, tempo de vida do cache, e o fato de que, no RAG, só a parte estável do prompt (instruções + regras de segurança) é cacheável, não os trechos recuperados.
- Cache de respostas para perguntas frequentes (ex.: "qual sua experiência com IA?").
- Escolha de modelo pequeno/barato para o chat, com limite de tokens de saída.
- Meta: custo mensal estimado próximo de zero para o tráfego típico de um portfólio.

## 5.5 Gestão de credenciais — requisitos
Credenciais envolvidas: chave da API do Google (Gemini), token do Hugging Face (modelo restrito do Prompt Guard 2), segredo compartilhado entre o backend (Vercel) e o Space, e segredos usados nos workflows do GitHub Actions.

Requisitos (proporcionais a um portfólio pessoal):
- **Chave do Google restrita:** limitada às APIs necessárias e com teto de cota/orçamento, para limitar o dano em caso de vazamento.
- **Endpoint do Space protegido** por segredo compartilhado (enviado em cabeçalho e comparado de forma segura), para que terceiros não usem o classificador.
- **Secret scanning e push protection** do GitHub ativados no repositório.
- **Workflows com `permissions:` mínimas**, e segredos apenas via *GitHub Secrets*.
- **`.env.example`** sem valores reais versionado; `.env` no `.gitignore`.
- **Segredos por ambiente:** chaves separadas para desenvolvimento e produção; cada segredo guardado só onde é usado (Vercel, GitHub Secrets, Hugging Face Secrets).
- **Resposta a vazamento (nota curta):** revogar a chave, gerar outra e atualizar nos locais de uso.
- Fora do escopo por ora: rotação periódica automatizada, fixação de actions por hash e regras para PRs de forks.

## 6. Direção técnica preliminar (será formalizada no `/speckit.plan`)
- **Frontend:** React (Next.js) + Tailwind CSS + TypeScript. *Projeto de aprendizado: o autor não tem experiência prévia com React.*
- **Backend:** Python + FastAPI (endpoint do chat RAG e formulário de contato).
- **Busca vetorial (RAG):** MVP com arquivo de embeddings pré-calculados + NumPy (similaridade de cosseno), sem banco externo. A busca fica atrás de uma interface pequena (`VectorStore.search(query_embedding, lang, top_k)`), preparada para migrar depois para o Qdrant (Cloud, camada gratuita) sem alterar o restante do código. Riscos do Qdrant a considerar na migração: suspensão do cluster gratuito por inatividade. Chroma fica restrito ao uso local de estudo, por não se adequar ao ambiente serverless da Vercel.
- **LLM:** padrão inicial Google Gemini Flash Lite (API já disponível ao autor). Groq permanece como alternativa a avaliar (custo, latência, limites gratuitos e hospedagem de modelos de guardrail). Decisão em aberto, mas o backend deve isolar o provedor atrás de uma interface (`LLMClient`) para permitir a troca por configuração, como na busca vetorial.
- **Hospedagem:** Vercel, priorizando o menor custo. Ponto a validar: viabilidade do backend Python e do vetor de busca em funções serverless da Vercel.
- **Repositório:** GitHub.

## 7. Restrições
- Baixo custo: uso de camadas gratuitas sempre que possível; custo de LLM limitado.
- Conteúdo pessoal (foto, CV) é fornecido por mim.
- Por ser um projeto de aprendizado, o código deve ser claro e comentado onde ajudar a compreender React.

## 8. Critérios de sucesso
- Um recrutador entende quem sou e minha área de atuação na tela inicial, sem rolar a página.
- Todas as seções funcionam bem em celular e desktop, em ambos os idiomas e temas.
- O chat responde corretamente perguntas sobre minha carreira, sem inventar informações.
- Lighthouse acima de 90 em desempenho, acessibilidade e SEO.
- Portal publicado na Vercel com endereço estável.

## 9. Fora do escopo (por ora)
- Blog, painel administrativo, login de usuários, analytics avançado de marketing (a observabilidade do chat da seção 5.3 está no escopo).

## 10. Pendências
- Referência(s) visual(is) de portfólio.
- Domínio próprio (ou usar o subdomínio da Vercel).
- Foto, CV, lista de projetos e certificações a incluir.
- Provedor de LLM/embeddings para o RAG (decidir no plano).
