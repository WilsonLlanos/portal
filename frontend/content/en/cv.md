<!-- This file feeds the chat's knowledge base (ingest.py); it is not shown on the page.
     It keeps the details that the page's timeline only summarizes. -->

# CV — Wilson Llanos (EN)

## Background

Wilson is a Systems Developer at EISA - Empresa Interagrícola, building production generative AI
solutions on the Azure ecosystem with a focus on data security and governance. He has built a
multi-agent system with LangGraph and MCP for IT incident triage and is currently building a
multi-agent system with hybrid RAG to automate tier-1 support for a coffee logistics platform. He
also works on data integration across four systems, including legacy ones, eliminating recurring
errors, and has Machine Learning projects with Apache Spark on Databricks.

Besides that, this very portal is another example of relevant work: it offers an AI agent that
helps visitors ask questions about Wilson's career and highlights relevant information the visitor
shares during the conversation.

## Main projects

### Multi-agent system for IT incidents (completed, 2026)
Python, LangGraph, MCP, Azure AI Foundry, Azure AI Search, Azure SQL. Wilson built a multi-agent
system focused on automatic IT incident triage and on reducing response time (MTTR). He implemented
asynchronous route orchestration and state control with LangGraph, with secure communication
through the MCP (Model Context Protocol) pattern. He connected Azure AI Foundry reasoning to the
operational context via RAG with Azure AI Search, using Azure SQL for memory persistence and
auditing. He adopted Spec-Driven Development (SDD) to govern agent behavior, with explicit tool
contracts and layered human approval to restrict agent scope and mitigate unsupervised execution
risks.

### Multi-agent hybrid RAG for tier-1 support automation (in progress, 2026)
LangGraph, Azure AI Foundry, Azure AI Search, Azure SQL. A multi-agent system with hybrid RAG to
automate tier-1 support for a coffee logistics platform, combining vector search (Azure AI Search)
and relational database queries (Azure SQL) via tool calling, with reasoning on Azure AI Foundry.
It includes a governance and security layer with Microsoft Presidio for dynamic anonymization of
personal data (LGPD), plus telemetry and cost tracking (FinOps) on Azure Application Insights.

### Portfolio Portal with AI Chat (personal, open source)
Repository: github.com/WilsonLlanos/portal. It is this very website: a bilingual (PT/EN) portfolio
with an AI assistant that answers questions about Wilson's career using RAG over his résumé.
Frontend in Next.js and TypeScript; backend in FastAPI with Gemini; vector search over precomputed
embeddings; Llama Prompt Guard 2 guardrail against prompt injection, with safe degradation;
per-visitor question limit and daily cost cap on Upstash Redis; CI/CD with GitHub Actions and
deployment on Vercel. It was built with Spec-Driven Development (Spec Kit).

### Multi-agent merchant support — Getnet case (technical challenge, open source)
Repository: github.com/WilsonLlanos/getnet-multi-agent-support-system. Built as a technical
challenge for a hiring process: a support service for Getnet card-machine merchants with a single
endpoint, where a LangGraph router classifies each message and sends it to specialized agents. The
knowledge agent runs RAG over approved sources (Chroma with local multilingual embeddings) and
calls external APIs (Brazilian Central Bank PTAX exchange rate and weather); the support agent
answers from the merchant's own data through tools; an escalation agent records hand-offs to human
support. It has guardrails with standardized reasons, personal-data redaction, prompt-injection
checks and observability with structured logs. When context is insufficient, the system admits
the limitation instead of making things up. Technologies: Python, FastAPI, LangGraph, LangChain,
Claude, Chroma, Sentence Transformers, Docker. It was also built with Spec-Driven Development.

### Retrieval quality evaluation (used at EISA, open source)
Repository: github.com/WilsonLlanos/rag-doc-quality. A command-line tool created for EISA's tier-1
support RAG project: it indexes the documentation corpus and measures search quality before
publishing it to Azure AI Search. It compares vector and hybrid search (vector + BM25, fused with
RRF), runs a golden set of questions with Recall@k and MRR, compares results with a saved baseline
and lists the questions that failed. Technologies: Python, Azure OpenAI (embeddings), Qdrant,
fastembed (BM25) and Typer.

## Career progression at EISA - Empresa Interagrícola

Wilson built his tech career at EISA with successive promotions.

### Systems Developer (since Jan 2026)
- Building an AI solution with a multi-agent system (LangGraph) and hybrid RAG on Azure to automate
  tier-1 support for a coffee logistics platform.
- Built event-driven communication (Azure Service Bus + .NET), improving integration monitoring.
- Manages critical integrations between the ERP and logistics systems, syncing 50k+ records per day
  with 99.9% accuracy.
- Optimized an SSIS ETL pipeline, drastically reducing processing time.
- Implemented bidirectional flows to migrate 70+ processes with zero downtime.

### Programmer Analyst (Feb 2025 to Dec 2025)
- Built ETL processes (Azure Functions, SSIS) handling 1M+ records per month with 99.8% accuracy.
- Created analytical reports (Reporting Services, Crystal Reports) covering the entire commodity
  logistics process.
- Started his first generative AI prototypes with RAG and LLMs.
- Was promoted to Systems Developer after exceeding goals and delivering ahead of schedule.

### Support Analyst (Apr 2022 to Jan 2025)
- Provided technical support to users, diagnosing and solving system, database and infrastructure
  issues, reducing recurring tickets.

## Education and certifications

The "ETL Pipelines and Machine Learning with Apache Spark" course from Data Science Academy
(completed in January 2025) was Wilson's starting point in the AI world.

Wilson completed an MBA in Artificial Intelligence and Big Data at ICMC/USP (2025-2026, completed
in October 2026) and holds a Bachelor's in Civil Engineering from Uninove (2012-2016).
His certifications are Microsoft Certified: Azure Data Fundamentals (DP-900) and "ETL Pipelines and
Machine Learning with Apache Spark", from Data Science Academy.

## Working philosophy

"The question isn't just building software, but building and maintaining it efficiently and
securely, always thinking about what's best for each project. That's exactly what I bring to my
solutions. In a recent project, where I'm implementing an automated support solution for users of
a complex system on Azure, there will be an integration of the LLM with two different types of
databases (vector and relational) — an engineering challenge that has been overcome."


## Outside of work (personal interests)

In his free time, Wilson plays guitar, plays Counter-Strike and follows AI news. He also meditates,
which helps him stay focused. He likes to stay current by trying out new technologies and, from time
to time, goes back to the fundamentals of the field to stay sharp on the front line.
