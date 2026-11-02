# Research: Observabilidade do Chat com Trace Completo e Avaliação Automática

Decisões técnicas da feature [002-chat-observability](spec.md). Base: Langfuse Python SDK **4.15.6** (instalado em `backend/.venv`, API inspecionada diretamente) e a documentação atual do Langfuse (outubro de 2026).

## R1. Como criar o trace: observações explícitas, sem contexto implícito

- **Decision**: criar a observação raiz com `client.start_observation(...)` e as filhas com `parent.start_observation(...)`, encerrando cada uma com `.update(...)` + `.end()`. **Não** usar `@observe`, `start_as_current_observation` nem nenhum context manager que atravesse um `yield`.
- **Rationale**: `run_chat_pipeline` é um gerador. O primeiro `next()` roda no handler assíncrono (`backend/app/api/chat.py`) e os seguintes rodam no threadpool do `StreamingResponse`, cada um em um contexto copiado. Um contexto OpenTelemetry aberto antes de um `yield` e fechado depois disso estaria em outro `Context`, o que gera o erro "Failed to detach context" e deixa spans órfãos. Com observações explícitas, quem liga pai e filho são as referências do Python, não o contexto da thread.
- **Alternatives considered**: o decorador `@observe` no pipeline (quebra com geradores e threads); `start_as_current_observation` (mesmo problema); a integração automática do Gemini via OpenTelemetry (não cobre guardrail, busca nem a sanitização, e envia a pergunta crua).

## R2. Atributos do trace (sessão, nome, idioma, versão da base)

- **Decision**: usar `langfuse.propagate_attributes(session_id=..., trace_name="chat-turn", metadata={"lang": ..., "kb_version": ...})` **apenas em volta da criação de cada observação**, em blocos `with` curtos e sem `yield` dentro. Isso fica encapsulado num helper do tracer (R8).
- **Rationale**: no SDK v4, `propagate_attributes` é a forma recomendada de definir `session_id` e o nome do trace. Ela aplica os atributos às observações criadas dentro do bloco, e o painel só agrega por sessão as observações que têm o atributo. Reabrir o bloco a cada criação garante o atributo em todas as etapas sem manter contexto aberto entre `yield`s.
- **Verificação obrigatória** (quickstart, cenário 2): confirmar no painel que a sessão aparece no trace e nas etapas. Se o atributo não se propagar para filhas criadas por `parent.start_observation`, o mínimo aceitável é a sessão no trace (é o que a visão *Sessions* usa).
- **Resultado da verificação** (2026-11-01, cenário 2): a visão *Sessions* agrupou os traces e somou custo e tokens que só existem na etapa `answer`, o que indica que o atributo chega às etapas filhas. A verificação foi feita por essa soma, não abrindo o atributo em cada etapa.
- **Alternatives considered**: um único `with propagate_attributes` em volta do pipeline inteiro (atravessaria `yield`s, R1); passar `session_id` por `**kwargs` de `update()` (comportamento não documentado).

## R3. Tipos e nomes das observações

- **Decision**: uma raiz e quatro etapas, usando os tipos nativos do SDK v4:

  | Etapa | Nome | `as_type` |
  |---|---|---|
  | Raiz da interação | `chat-turn` | `span` |
  | Guardrail | `guardrail` | `guardrail` |
  | Embedding da pergunta | `embed-question` | `embedding` |
  | Busca | `retrieval` | `retriever` |
  | Geração | `answer` | `generation` |

- **Rationale**: com os tipos nativos, o painel mostra ícones e filtros por tipo, e só `generation`/`embedding` entram nos agregados de custo e tokens. A estrutura detalhada está em [contracts/trace-structure.md](contracts/trace-structure.md).

## R4. O que o juiz avalia: a observação raiz, não a geração

- **Decision**: a regra de avaliação mira a **observação raiz `chat-turn`**, filtrada por "Is Root Observation" + nome `chat-turn` + `metadata.outcome` em (`answered`, `no_answer`). A raiz guarda em `input` a pergunta sanitizada e em `output` a resposta final.
- **Rationale**: na avaliação online, o juiz só enxerga `input`, `output` e `metadata` da observação avaliada; ele não carrega outras observações do mesmo trace. A `input` da geração contém o system prompt inteiro, os trechos e o histórico: são mais tokens (custo) e mais ruído para classificar. A raiz tem exatamente pergunta + resposta. Perguntas recusadas pelo guardrail, limitadas ou pausadas não têm resposta do LLM e ficam fora pelo filtro de `outcome`.
- **Consequência na spec**: FR-010 dizia "pergunta e resposta registradas na etapa de geração". O texto foi ajustado para "registradas no registro da interação", sem mudar a intenção.
- **Alternatives considered**: avaliar a geração com mapeamento de subcampos (a documentação não oferece seleção por JSONPath); colocar a pergunta crua em `metadata` da geração (duplicaria dados e exigiria outra sanitização).

## R5. Maior nota de similaridade como métrica

- **Decision**: registrar a maior nota como **score numérico do trace** (`retrieval_top_score`, via `root.score_trace(..., data_type="NUMERIC")`), além de colocá-la em `metadata` da etapa `retrieval` com todas as notas.
- **Rationale**: scores são filtráveis e aparecem nas análises do painel, inclusive cruzados com o score categórico do juiz (US3, cenário 3). Valores em `metadata` propagado viram texto de até 200 caracteres, o que não serve para comparação numérica.
- **Custo**: 1 unidade extra por pergunta (R11).

## R6. Custo, tokens e tempo até o primeiro token

- **Decision**: na etapa `answer`, enviar `model=settings.gemini_model`, `model_parameters` (temperatura, máximo de tokens), `usage_details={"input": n, "output": n}`, `cost_details` em **dólares**, calculado com os mesmos preços que o teto diário já usa (`_INPUT_COST_CENTS_PER_MTOK` / `_OUTPUT_COST_CENTS_PER_MTOK` em `pipeline.py`), e `completion_start_time` marcado no primeiro trecho de texto recebido do LLM.
- **Rationale**: o Langfuse infere custo por uma tabela de preços que pode não ter `gemini-3.1-flash-lite`. Enviar o custo explícito mantém o painel igual ao valor que controla o teto diário (uma única fonte). `completion_start_time` é o campo que o Langfuse usa para calcular o tempo até o primeiro token.
- **Alternatives considered**: deixar o Langfuse inferir o custo (risco de custo zero ou divergente); cadastrar o modelo e o preço no painel (passo manual que fica desatualizado).

## R7. Sanitização: todo texto que pode conter dado do visitante, feita pelo tracer

- **Decision**: mover a sanitização para `backend/app/observability/sanitize.py` e aplicá-la a todo texto que pode conter um dado digitado pelo visitante: a pergunta, **todas** as mensagens do histórico (as do assistente também) e a **resposta atual**, completa, parcial ou de recusa, porque o modelo pode repetir um e-mail ou telefone da pergunta ("Anotei seu contato joao@…"). E-mails viram `[email]`. Sequências com **9 ou mais dígitos**, aceitando espaços, pontos, traços e parênteses no meio, viram `[número]`. Quem sanitiza é o **tracer** (R8): o pipeline passa os textos originais e cada método da fachada sanitiza antes de gravar. O visitante continua recebendo a resposta original. O system prompt e os trechos recuperados **não** são sanitizados.
- **Rationale**: a regra atual (`\+?\d[\d\s().-]{6,}\d`) também troca intervalos de datas como `2019-2024` (8 dígitos), que aparecem em perguntas legítimas. Com o limite de 9 dígitos, anos e intervalos de anos ficam preservados, e celulares sem DDD (9 dígitos), telefones com DDD e CPF (11) continuam sendo pegos. Concentrar a sanitização no tracer evita que um campo novo seja gravado cru por esquecimento. Sanitizar a resposta tem um custo pequeno: um contato público do autor citado na resposta também vira marcador no painel, o que não atrapalha a depuração nem o juiz. Os trechos são conteúdo público do autor e o painel é privado (premissa da spec).
- **Alternatives considered**: a máscara global do SDK (`Langfuse(mask=...)`), que também alteraria os trechos e o system prompt (as datas das experiências virariam `[número]` em toda etapa de busca e geração); sanitizar no pipeline, campo a campo (cada campo novo seria um ponto de esquecimento).

## R8. Fachada do tracer, tolerância a falha e envio

- **Decision**: criar `backend/app/observability/tracing.py` com um `ChatTracer` que abre uma `ChatTurnTrace` por pergunta e expõe métodos por etapa (`guardrail`, `embedding`, `retrieval`, `generation_started`, `first_token`, `generation_finished`, `finish`, `flush`). Há duas implementações: `LangfuseChatTurnTrace` e `NoopChatTurnTrace`, usada quando as chaves não estão configuradas (dev e CI). Toda chamada ao SDK fica em `try/except` e, em caso de falha, só registra `observability.trace_failed` no log. O ciclo de vida separa **encerrar** de **enviar**:
  - `finish(...)` encerra a raiz **localmente, sem rede**, e é idempotente. O pipeline o chama **antes do último evento** de cada caminho (`done` ou `error`).
  - `flush()` envia os dados e roda **depois do último evento**, no código que vem após o último `yield`. Esse código só roda quando o consumidor pede o próximo item: no streaming, é o `StreamingResponse`, depois de enviar o `done` ou o `error`. Quando o primeiro evento já é um erro (pausa, limite por hora, LLM indisponível antes do primeiro token), o `chat.py` devolve o 429/503 e consome o resto do gerador numa `BackgroundTask`, que o Starlette só executa depois de enviar a resposta.
  - O `finally` do pipeline só encerra traces **ainda abertos**, o que só acontece quando o gerador é fechado no meio do streaming (o visitante desconectou): `outcome = "disconnected"`, com `level="WARNING"`. O outcome próprio deixa a resposta parcial fora da regra do juiz, que só avalia `answered` e `no_answer`. Nesse caso não há `flush` síncrono, porque o fechamento pode ocorrer em qualquer thread, inclusive no loop de eventos. O exportador em segundo plano do SDK envia o trace no ciclo seguinte (`flush_interval`, 5 s por padrão), em melhor esforço.
  - O cliente é criado com `timeout=2` (segundos) e `should_export_span=is_langfuse_span`. Assim, só as observações criadas pela fachada são exportadas: o filtro padrão também exportaria spans de LLM de outras bibliotecas instrumentadas, com texto não sanitizado. Hoje nenhuma dependência do backend emite esses spans, mas o filtro evita a surpresa no futuro.
- **Rationale**: atende FR-009 e SC-003, porque nada do Langfuse fica no caminho até o primeiro token. Também atende o Princípio VI (fachada didática e substituível, como `LLMClient`/`VectorStore`) e o Princípio VII (os testes de CI usam o Noop ou um dublê, sem rede). O `flush()` explícito é necessário em serverless, onde a instância pode congelar logo após a resposta. Encerrar o trace antes do último evento o mantém correto mesmo que o gerador nunca seja retomado. Hoje o `chat.py` abandona o gerador quando o primeiro evento é um erro: um `finally` que dependesse disso só rodaria na coleta de lixo, marcaria uma desconexão que não houve e faria o `flush` durante o encerramento do handler, atrasando o 429/503 quando o Langfuse estivesse lento.
- **Substitui** `log_chat_interaction` (evento único, `langfuse_client.py`). O log JSON estruturado `chat.interaction` continua sendo emitido quando o Langfuse está desabilitado, para não perder a observabilidade em dev.

## R9. Identificador de conversa (FR-017)

- **Decision**: no frontend, `useChatSession` cria o identificador com `crypto.randomUUID()` na primeira pergunta após a montagem do componente e o guarda em um `useRef`, **sem** gravar em `localStorage`, `sessionStorage` ou cookie. O valor vai como `conversation_id` em cada `POST /api/chat`. `crypto.randomUUID` só existe em contexto seguro (HTTPS ou `localhost`): quando ele não existe, como num teste pelo celular via IP da rede local, o campo é omitido e o chat funciona normalmente, sem agrupamento. A geração preguiçosa também evita criar um UUID novo a cada renderização, o que aconteceria com `useRef(crypto.randomUUID())`. No backend, `ChatRequest.conversation_id` é opcional e aceito **só** no formato UUID. Valores fora do formato são descartados em silêncio (viram `None`), sem 422. O valor vira o `session_id` do trace.
- **Rationale**: o identificador some ao recarregar a página e não tem ligação com IP ou navegador (Princípio IV). Validar o formato impede que alguém use o campo para injetar texto livre (inclusive dados pessoais) no painel. Descartar em vez de recusar segue o padrão do histórico, que é truncado, não recusado.
- **Contrato**: [contracts/chat-api-delta.md](contracts/chat-api-delta.md).

## R10. Configuração do juiz no Langfuse

- **Decision**: uma **LLM connection** do tipo Google AI Studio, com uma chave do Gemini **exclusiva do juiz** (restrita à Generative Language API, Princípio IX), criada num **projeto do Google Cloud separado** do chat: no Gemini, a cota e os limites valem por projeto, não por chave, e o faturamento também é separado por projeto. Na conexão, um **avaliador customizado** com score **categórico** `content_coverage` e categorias `respondeu`, `lacuna` e `recusa`. Modelo do juiz: o mesmo validado pelo teste de referência (R12), por padrão `gemini-3.1-flash-lite`; se ele não estiver na lista do Langfuse, escolhe-se o Flash-Lite disponível e o teste roda de novo com ele. Amostragem inicial: 100%. O texto do critério fica versionado em `backend/app/observability/judge_prompt.md`, que é a fonte única colada no painel e lida pelo teste. Esse texto não fixa formato de saída: o Langfuse acrescenta as próprias instruções de saída estruturada, e o teste usa a saída estruturada do `google-genai`.
- **Rationale**: as avaliações por LLM-como-juiz estão incluídas no plano Hobby; o Langfuse aceita Google AI Studio como provedor e scores categóricos com categorias definidas. Detalhes e passo a passo em [contracts/judge-evaluator.md](contracts/judge-evaluator.md).
- **Custo estimado do juiz** (estimativa própria, não da documentação): cerca de 1.000 tokens de entrada (critério + pergunta + resposta) e 100 de saída por avaliação, o que dá aproximadamente US$ 0,0004 com Flash-Lite. Com 1.000 perguntas por mês, fica em torno de US$ 0,40, abaixo do limite de SC-006. Se o tráfego crescer, reduz-se a amostragem.

## R11. Volume no plano Hobby

- **Decision**: estimativa de cerca de **10 unidades por pergunta respondida**: trace, 5 observações (raiz + 4 etapas), 2 scores (`retrieval_top_score` e `content_coverage`) e o trace que cada execução do juiz cria no ambiente `langfuse-llm-as-a-judge`. Esse trace do juiz entra na conta como 2 unidades, por precaução: a documentação não diz se ele é cobrado. Perguntas recusadas, limitadas ou pausadas geram de 2 a 3 unidades. Os testes locais (ambiente `development`, R14) consomem a mesma cota.
- **Rationale**: no Hobby (50 mil unidades por mês, sem excedente), 1.000 perguntas consomem cerca de 10 mil unidades, bem abaixo do limite (SC-006). O limite só seria atingido perto de 5 mil perguntas por mês. O cenário 10 do quickstart confere o número real.

## R12. Validação do juiz (SC-004)

- **Decision**: um conjunto de referência `backend/tests/eval/judge_reference.jsonl` com no mínimo 21 pares pergunta/resposta rotulados (7 por categoria), e o teste `backend/tests/eval/test_judge_accuracy.py`. O teste aplica o mesmo `judge_prompt.md` via Gemini com a chave do juiz (`GEMINI_JUDGE_API_KEY` no ambiente) e verifica as metas de SC-004: pelo menos 90% de acerto e no máximo 1 recusa classificada como lacuna. Como os demais testes de `tests/eval`, ele é pulado sem a chave e fica fora do CI.
- **Rationale**: valida o critério de avaliação de forma reproduzível e barata, sem depender do painel. Como o painel usa o mesmo texto, um critério aprovado no teste é o critério em produção.
- **Alternatives considered**: datasets e experimentos do Langfuse (mais configuração manual, e o critério ficaria só no painel).

## R13. Retenção e privacidade

- **Decision**: sem mudança. A retenção de 30 dias do Hobby continua cumprindo FR-022 da feature 001; o aviso de privacidade do chat já cobre o registro das perguntas.

## R14. Separação entre desenvolvimento e produção

- **Decision**: dois pares de chaves do Langfuse no mesmo projeto, um para desenvolvimento (em `backend/.env`) e outro para produção (na Vercel), e o atributo de ambiente do Langfuse: `LANGFUSE_TRACING_ENVIRONMENT` = `development` localmente e `production` na Vercel. O valor é lido pelo `Settings` e passado explicitamente ao cliente (`Langfuse(environment=...)`), porque o `pydantic-settings` lê o `.env` sem exportá-lo para as variáveis do processo, que é onde o SDK procuraria. A raiz `chat-turn` também grava `metadata.environment`, e a regra do juiz filtra `metadata.environment = production`.
- **Rationale**: o Princípio IX exige chaves separadas para desenvolvimento e produção: revogar a de desenvolvimento não derruba a produção. Sem a separação, os testes locais seriam avaliados pelo juiz (dados pessoais falsos do cenário 4, ataques do cenário 3, perguntas repetidas), poluiriam a lista de lacunas e gastariam a cota do juiz. As telas do painel filtram por ambiente, mas a documentação das regras de avaliação não confirma esse filtro; por isso o valor é repetido em `metadata`, campo que as regras filtram. Consequência: o juiz só avalia o portal publicado, e os cenários 5 e 6 do quickstart são validados lá.
- **Alternatives considered**: um projeto do Langfuse por ambiente (isolamento total, mas duplica a configuração, e o limite de projetos do Hobby não foi confirmado); um único par de chaves para os dois ambientes (viola o Princípio IX).
