"use client";

import { useCallback, useRef, useState } from "react";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export type ChatErrorCode =
  | "empty_message"
  | "message_too_long"
  | "rate_limited"
  | "chat_paused"
  | "unavailable";

interface ChatState {
  messages: ChatMessage[];
  isStreaming: boolean;
  error: { code: ChatErrorCode; message: string } | null;
  suggestions: string[];
}

const MAX_HISTORY_TURNS = 4; // FR-013a: memória curta, só durante a visita

/**
 * T054: cliente do chat via SSE, com memória curta em memória do navegador
 * (nunca persistida — FR-013a). T061: `locale` é repassado em cada chamada
 * para que o chat responda no idioma selecionado (FR-016).
 */
export function useChatSession(locale: string) {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isStreaming: false,
    error: null,
    suggestions: [],
  });
  const abortRef = useRef<AbortController | null>(null);

  const send = useCallback(
    async (text: string) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      const history = state.messages.slice(-MAX_HISTORY_TURNS);
      const userMessage: ChatMessage = { role: "user", content: text };

      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage, { role: "assistant", content: "" }],
        isStreaming: true,
        error: null,
        suggestions: [],
      }));

      try {
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text, lang: locale, history }),
          signal: controller.signal,
        });

        if (!response.ok) {
          const body = await response.json().catch(() => null);
          setState((prev) => ({
            ...prev,
            isStreaming: false,
            messages: prev.messages.slice(0, -1), // remove o balão vazio do assistente
            error: {
              code: body?.code ?? "unavailable",
              message: body?.message ?? "",
            },
          }));
          return;
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("sem corpo de resposta");
        const decoder = new TextDecoder();
        let buffer = "";

        // Parser simples de SSE: eventos separados por linha em branco,
        // cada um com "event: <tipo>" e "data: <json>".
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          const parts = buffer.split("\n\n");
          buffer = parts.pop() ?? "";

          for (const part of parts) {
            const eventLine = part.split("\n").find((l) => l.startsWith("event:"));
            const dataLine = part.split("\n").find((l) => l.startsWith("data:"));
            if (!eventLine || !dataLine) continue;

            const eventType = eventLine.replace("event:", "").trim();
            const data = JSON.parse(dataLine.replace("data:", "").trim());

            if (eventType === "token") {
              setState((prev) => {
                const messages = [...prev.messages];
                const last = messages[messages.length - 1];
                messages[messages.length - 1] = {
                  ...last,
                  content: last.content + data.text,
                };
                return { ...prev, messages };
              });
            } else if (eventType === "done") {
              setState((prev) => ({
                ...prev,
                isStreaming: false,
                suggestions: data.suggestions ?? [],
              }));
            } else if (eventType === "error") {
              setState((prev) => ({
                ...prev,
                isStreaming: false,
                messages: prev.messages.slice(0, -1),
                error: { code: data.code, message: data.message },
              }));
            }
          }
        }
      } catch (err) {
        if ((err as Error).name === "AbortError") return;
        setState((prev) => ({
          ...prev,
          isStreaming: false,
          error: { code: "unavailable", message: "" },
        }));
      } finally {
        setState((prev) => ({ ...prev, isStreaming: false }));
      }
    },
    [locale, state.messages],
  );

  return { ...state, send };
}
