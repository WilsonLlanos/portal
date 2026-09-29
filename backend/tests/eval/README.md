# Conjuntos de avaliação (SC-003, SC-007)

Estes testes fazem chamadas **reais** ao Gemini e à Groq (não usam dublês),
para validar de ponta a ponta os critérios de sucesso SC-003 (acerto do
chat) e SC-007 (resistência a manipulação). Por isso:

- São **pulados automaticamente** (`pytest.skip`) se `GEMINI_API_KEY` (e, para
  o guardrail real, `GROQ_API_KEY`) não estiverem configuradas — não quebram
  o CI de quem não tiver as chaves.
- Exigem a base de conhecimento gerada (`uv run python scripts/ingest.py`).
- Têm **custo real**, ainda que pequeno.

`questions.jsonl` e `attacks.jsonl` são um ponto de partida (poucos itens,
baseados no conteúdo placeholder). **Expandir para dezenas de itens** assim
que o conteúdo real do autor (bio, projetos, certificações) estiver em
`frontend/content/`, para que os 95%/100% de SC-003 e a "grande maioria" de
SC-007 sejam estatisticamente significativos.
