<!--
Sync Impact Report
- Version change: 1.1.0 → 1.1.1 (PATCH: correção de redação desatualizada, sem mudança de regra)
- Modified principles:
  - VII. CI/CD e Automação — "ping agendado" generalizado para "verificação de saúde/disponibilidade
    agendada de um serviço externo crítico (quando aplicável)", pois a arquitetura vigente (Groq,
    sem Hugging Face Space) não tem mais um serviço que "dorme" e precise de ping; a regra de fundo
    (primeiro workflow = checagem agendada de disponibilidade) não mudou.
  - IX. Gestão de Credenciais — removida a menção específica a "segredo do Space" e "Hugging Face
    Secrets"; generalizada para "cofre nativo de qualquer serviço externo usado pelo projeto" e
    "qualquer endpoint próprio exposto pelo projeto MUST exigir autenticação ou segredo
    compartilhado", cobrindo tanto a arquitetura atual (sem Space) quanto futuras mudanças de
    provedor sem exigir nova emenda a cada troca.
- Added sections: none
- Removed sections: none
- Deferred TODOs: none
- Motivação: achados C1 e C2 da análise `/speckit-analyze` de 2026-09-27 sobre
  specs/001-portfolio-portal (texto da constituição referenciando um componente — Hugging Face
  Space — descartado no plano de implementação em favor da API da Groq).
-->
# Portal de Portfólio (IA) Constitution

## Core Principles

### I. Veracidade
O chat MUST responder apenas com base no conteúdo recuperado da base de conhecimento do autor
(CV, projetos, certificações) e MUST admitir explicitamente quando não souber. É proibido
inventar experiências, datas, tecnologias ou credenciais.
Rationale: o portal serve a recrutadores; uma informação falsa sobre o autor destrói a
credibilidade do projeto inteiro.

### II. Custo Mínimo
Camadas gratuitas e soluções simples MUST ser priorizadas. Todo custo variável (chamadas a
LLM, embeddings, serviços externos) MUST ter um limite explícito (rate limit, teto de tokens,
tamanho máximo de input).
Rationale: o portal é público e um abuso não pode gerar cobrança inesperada.

### III. Segurança em Camadas
As defesas do chat MUST ser combinadas: guardrail de entrada (Llama Prompt Guard 2), limite de
tamanho do input, rate limit e system prompt restrito ao contexto recuperado. Quando o
guardrail estiver indisponível, o sistema MUST degradar de forma segura (fail-open com
defesas locais mais restritas e evento registrado), com timeout curto e circuit breaker.
Segredos MUST NOT ser versionados; usar variáveis de ambiente e GitHub Secrets.
Rationale: nenhuma defesa isolada é suficiente, e a experiência do visitante não deve quebrar
por falha de um serviço auxiliar.

### IV. Privacidade
A coleta MUST ser mínima, sem dados pessoais, com aviso claro ao visitante de que as perguntas
do chat são registradas e com retenção curta dos registros.
Rationale: transparência e proporcionalidade para um site pessoal.

### V. Acessibilidade e Desempenho
A interface MUST ser mobile-first, bilíngue (PT-BR e EN), com temas claro e escuro, navegação
por teclado e contraste adequado. A meta é Lighthouse acima de 90 em desempenho,
acessibilidade e SEO.
Rationale: o primeiro contato do recrutador é rápido e frequentemente pelo celular.

### VI. Código Didático e Substituível
O código MUST priorizar clareza e conter comentários úteis, pois o autor está aprendendo React.
Provedores externos (LLM, busca vetorial, guardrail) MUST ficar atrás de interfaces
(`LLMClient`, `VectorStore`, `InputGuard`), permitindo troca por configuração.
Rationale: o projeto é também veículo de aprendizado, e a troca de provedores é uma
possibilidade real prevista.

### VII. CI/CD e Automação
Toda mudança MUST passar por CI (lint, testes e build) antes de entrar na `main`, e a `main`
MUST ser protegida contra merge com CI falhando. O deploy na Vercel é automático a cada push
na `main`; NÃO se cria pipeline de deploy próprio para o que a Vercel já faz. Workflows do
GitHub Actions MUST ser pequenos, legíveis e proporcionais ao projeto, adotados em ordem
crescente: verificação de saúde/disponibilidade agendada de um serviço externo crítico (quando
aplicável — por exemplo, um ping ou uma checagem de `/health`), CI do frontend, CI do backend,
regeneração de embeddings, proteção da `main`. Workflows agendados MUST falhar de forma
explícita e ter mitigação contra desativação por inatividade.
Rationale: automação confiável com o menor custo de manutenção, e prática de CI/CD como
objetivo de aprendizado. A redação não amarra o projeto a um serviço específico (ex.: um Space
que "dorme"), para que a regra continue válida se o provedor de guardrail ou de hospedagem
mudar.

### VIII. Observabilidade e Testes Proporcionais
O chat MUST ser rastreado (pergunta, trechos recuperados, resultado do guardrail, latência,
custo e erros) e a saúde dos serviços monitorada, sem coletar dados pessoais. Os testes MUST
cobrir a lógica crítica (busca, guardrails, política de falha) em vez de perseguir cobertura
total.
Rationale: em sistemas de IA, sem visibilidade não há como detectar lacunas de conteúdo,
abuso ou regressões de qualidade.

### IX. Gestão de Credenciais
Credenciais de provedores externos (ex.: LLM, embeddings, guardrail, cache/rate limit,
observabilidade) MUST viver apenas em variáveis de ambiente ou no cofre nativo de cada
plataforma usada (ex.: Vercel, GitHub Secrets, ou o cofre do próprio provedor), com chaves
separadas para desenvolvimento e produção. Toda chave de provedor externo MUST ser restrita ao
mínimo necessário (escopo de API) e ter teto de cota ou de orçamento quando o provedor
oferecer essa opção. Qualquer endpoint próprio exposto pelo projeto MUST exigir autenticação ou
segredo compartilhado. O repositório MUST ter secret scanning e push protection ativados e um
`.env.example` sem valores reais. Workflows do GitHub Actions MUST declarar `permissions:`
mínimas. Em caso de vazamento, a chave MUST ser revogada e substituída imediatamente.
Rationale: um vazamento de chave gera custo e abuso; as medidas acima são gratuitas e
suficientes para o porte do projeto (rotação automatizada e regras para forks ficam fora do
escopo por ora). A redação não lista provedores específicos, para que a regra continue valendo
sem emenda quando um provedor for trocado (ex.: a substituição do Hugging Face Space pela API
da Groq no guardrail).

## Restrições Adicionais

- O projeto MUST manter custo mensal próximo de zero para o tráfego típico de um portfólio.
- O conteúdo pessoal (foto, CV, projetos, certificações) é fornecido pelo autor; nenhum
  conteúdo sobre o autor é gerado sem fonte.
- O escopo exclui blog, painel administrativo e login de usuários, salvo emenda a esta
  constituição ou nova especificação aprovada.
- Decisões de stack são tomadas no plano de implementação, respeitando estes princípios; o
  `brief.md` registra a direção técnica preliminar.

## Fluxo de Desenvolvimento e Qualidade

- O desenvolvimento segue o fluxo Spec Kit: constituição, especificação, clarificação, plano,
  tarefas e implementação.
- Mudanças chegam à `main` por pull request com CI verde.
- Todo plano MUST incluir uma verificação de conformidade com esta constituição (Constitution
  Check); violações MUST ser justificadas na seção de complexidade do plano.
- Novos serviços ou dependências pesadas MUST ser justificados frente aos princípios II e VI.

## Governance

Esta constituição prevalece sobre outras práticas do projeto. Emendas MUST ser documentadas
neste arquivo, com atualização da versão e da data. O versionamento é semântico: MAJOR para
remoção ou redefinição incompatível de princípios; MINOR para novo princípio ou ampliação
material; PATCH para esclarecimentos e correções de redação. Revisões de plano e de pull
request MUST verificar a conformidade com estes princípios.

**Version**: 1.1.1 | **Ratified**: 2026-09-26 | **Last Amended**: 2026-09-27
