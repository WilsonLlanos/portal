# Contrato: mudança em `POST /api/chat`

Delta sobre [001 contracts/chat-api.openapi.yaml](../../001-portfolio-portal/contracts/chat-api.openapi.yaml). A implementação deve atualizar aquele arquivo com o campo abaixo.

## `ChatRequest`: novo campo opcional

```yaml
conversation_id:
  type: string
  format: uuid
  description: >
    Identificador aleatório da conversa atual, gerado no navegador
    (crypto.randomUUID) uma vez por abertura da página e mantido só em
    memória; agrupa as perguntas no painel de observabilidade (FR-017 da
    feature 002). Não identifica o visitante. Valores fora do formato UUID
    são ignorados pelo servidor (tratados como ausentes), sem erro 422.
```

- **Obrigatório?** Não. Clientes antigos (sem o campo) e navegadores sem `crypto.randomUUID` (página fora de HTTPS e de `localhost`) continuam funcionando: a pergunta é registrada sem agrupamento.
- **Validação**: aceito só se for um UUID válido (qualquer versão, sem distinguir maiúsculas e minúsculas). Caso contrário, o valor vira `None`.
- **Respostas**: nenhuma mudança visível. Códigos 200/400/429/503, corpos e eventos SSE `token`/`done`/`error` são os mesmos. Internamente, quando o primeiro evento é um erro (429/503), o servidor consome o resto do pipeline numa tarefa em segundo plano, que envia o trace depois de a resposta sair (research.md R8).

## Frontend (`frontend/components/chat/useChatSession.ts`)

- Gera o UUID na primeira pergunta após a montagem do hook e o guarda num `useRef`; os envios seguintes reutilizam o mesmo valor.
- Gera só quando `crypto.randomUUID` existe (contexto seguro: HTTPS ou `localhost`). Sem ele, omite o campo; o chat funciona igual.
- Envia `conversation_id` em todo `POST /api/chat` quando há valor.
- **Não** grava o valor em `localStorage`, `sessionStorage` nem cookie. Recarregar a página gera uma nova conversa.
