<!-- Este arquivo alimenta a base de conhecimento do chat (ingest.py); não é exibido na página.
     Guarda os detalhes que a trajetória da página mostra só em resumo. -->

# CV — Wilson Llanos (PT-BR)

## Trajetória

Wilson é Desenvolvedor de Sistemas na EISA - Empresa Interagrícola e constrói soluções de IA
generativa em produção no ecossistema Azure, com foco em segurança e governança de dados. Já
desenvolveu um sistema multiagente com LangGraph e MCP para a triagem de incidentes de TI e,
atualmente, desenvolve um sistema multiagente com RAG híbrido para automatizar o suporte N1 de uma
plataforma de logística de café. Também atua na integração de dados entre quatro sistemas,
incluindo legados, eliminando erros recorrentes, e tem projetos de Machine Learning com Apache
Spark no Databricks.

Além disso, este próprio portal é outro exemplo de projeto relevante: ele disponibiliza um agente
de IA que ajuda o visitante a tirar dúvidas sobre a carreira de Wilson e destaca informações
relevantes que o visitante compartilhar na conversa.

## Projetos principais

### Sistema multiagente para incidentes de TI (concluído, 2026)
Python, LangGraph, MCP, Azure AI Foundry, Azure AI Search, Azure SQL. Wilson desenvolveu um sistema
multiagente focado na triagem automática de incidentes de TI e na redução do tempo de resposta
(MTTR). Implementou a orquestração de rotas assíncronas e o controle de estados com LangGraph, com
comunicação segura pelo padrão MCP (Model Context Protocol). Conectou o raciocínio do Azure AI
Foundry ao contexto operacional via RAG com Azure AI Search, usando Azure SQL para persistência de
memória e auditoria. Adotou Spec-Driven Development (SDD) para governar o comportamento dos agentes,
com contratos explícitos de ferramentas e aprovação humana em camadas para restringir o escopo dos
agentes e mitigar riscos de execução sem supervisão.

### RAG híbrido multiagente para automação do suporte N1 (em andamento, 2026)
LangGraph, Azure AI Foundry, Azure AI Search, Azure SQL. Sistema multiagente com RAG híbrido para
automatizar o suporte N1 de uma plataforma de logística de café, combinando busca vetorial (Azure AI
Search) e consultas ao banco relacional (Azure SQL) via Tool Calling, com raciocínio no Azure AI
Foundry. Inclui camada de governança e segurança com Microsoft Presidio para anonimização dinâmica
de dados pessoais (LGPD), além de telemetria e rastreamento de custos (FinOps) no Azure Application
Insights.

## Progressão na EISA - Empresa Interagrícola

Wilson construiu sua carreira de tecnologia na EISA com promoções sucessivas.

### Desenvolvedor de Sistemas (desde jan/2026)
- Desenvolvendo solução de IA com sistema multiagente (LangGraph) e RAG híbrido no Azure para
  automatizar o suporte N1 de uma plataforma de logística de café.
- Desenvolveu comunicação orientada a eventos (Azure Service Bus + .NET), aprimorando o
  monitoramento das integrações.
- Gerencia integrações críticas entre o ERP e os sistemas logísticos, sincronizando mais de 50 mil
  registros por dia com 99,9% de precisão.
- Otimizou um pipeline ETL com SSIS, reduzindo drasticamente o tempo de processamento.
- Implementou fluxos bidirecionais para a migração de mais de 70 processos com zero downtime.

### Analista Programador (fev/2025 a dez/2025)
- Desenvolveu processos ETL (Azure Functions, SSIS) processando mais de 1 milhão de registros por
  mês com 99,8% de precisão.
- Criou relatórios analíticos (Reporting Services, Crystal Reports) para todo o processo logístico
  da commodity.
- Iniciou os primeiros protótipos de IA generativa com RAG e LLMs.
- Foi promovido a Desenvolvedor de Sistemas após superar metas, concluindo entregas antecipadamente.

### Analista de Suporte (abr/2022 a jan/2025)
- Prestou suporte técnico a usuários, diagnosticando e resolvendo problemas de sistemas, banco de
  dados e infraestrutura, reduzindo tickets recorrentes.

## Formação e certificações

O curso "Pipeline ETL e Machine Learning com Apache Spark", da Data Science Academy
(concluído em janeiro de 2025), foi o ponto de partida de Wilson no universo da IA.

Wilson faz MBA em Inteligência Artificial e Big Data pelo ICMC/USP (2025-2026, conclusão prevista
para outubro de 2026) e é bacharel em Engenharia Civil pela Uninove (2012-2016). Tem as
certificações Microsoft Certified: Azure Data Fundamentals (DP-900) e "Pipeline ETL e Machine
Learning com Apache Spark", pela Data Science Academy.

## Filosofia de trabalho

"A questão não é desenvolver, mas sim, desenvolver e manter com eficiência e segurança, pensando
o melhor para cada projeto. E é exatamente isso que adoto em minhas soluções. Em um projeto mais
recente, onde estou implementando uma solução de suporte automatizado para usuários de um sistema
complexo em ambiente Azure, onde haverá uma integração do LLM com dois tipos de bancos diferentes
(vetorial e relacional), um desafio de engenharia que foi superado."
