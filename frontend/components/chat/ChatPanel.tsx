"use client";

import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { ASK_AI_EVENT } from "./AskAiButton";
import { ChatError, ChatSuggestions, PrivacyNotice } from "./ChatNotices";
import { useChatSession } from "./useChatSession";

/**
 * T055: painel do chat (US3) — streaming, sugestões de próximo passo,
 * aviso de privacidade e mensagens de erro/limite.
 */
export function ChatPanel() {
  const locale = useLocale();
  const t = useTranslations("chat");
  const { messages, isStreaming, error, suggestions, send } = useChatSession(locale);
  const [draft, setDraft] = useState("");

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const text = draft.trim();
    if (!text || isStreaming) return;
    setDraft("");
    void send(text);
  };

  // Perguntas prontas vindas dos botões "Pergunte à IA" da trajetória.
  useEffect(() => {
    const onAskAi = (event: Event) => {
      const question = (event as CustomEvent<string>).detail;
      if (!question || isStreaming) return;
      void send(question);
    };
    window.addEventListener(ASK_AI_EVENT, onAskAi);
    return () => window.removeEventListener(ASK_AI_EVENT, onAskAi);
  }, [isStreaming, send]);

  return (
    <section id="chat" className="mx-auto max-w-2xl px-6 py-8 md:py-12">
      <h2 className="text-2xl font-semibold sm:text-3xl">{t("title")}</h2>

      <div
        className="mt-6 flex max-h-96 flex-col gap-3 overflow-y-auto rounded-2xl border border-[var(--border)] bg-[var(--card)] p-4"
        aria-live="polite"
      >
        {messages.map((message, index) => (
          <div
            key={index}
            className={
              message.role === "user"
                ? "self-end rounded-2xl rounded-br-sm bg-[var(--accent)] px-4 py-2 text-[var(--accent-foreground)]"
                : "self-start rounded-2xl rounded-bl-sm bg-[var(--background)] px-4 py-2"
            }
          >
            {message.content || (isStreaming && index === messages.length - 1 ? "…" : "")}
          </div>
        ))}
      </div>

      {error && <div className="mt-3"><ChatError code={error.code} /></div>}
      <ChatSuggestions items={suggestions} />

      <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
        <label htmlFor="chat-input" className="sr-only">
          {t("placeholder")}
        </label>
        <input
          id="chat-input"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder={t("placeholder")}
          maxLength={500}
          disabled={isStreaming}
          className="flex-1 rounded-full border border-[var(--border)] bg-[var(--background)] px-4 py-2"
        />
        <button
          type="submit"
          disabled={isStreaming || !draft.trim()}
          className="rounded-full bg-[var(--accent)] px-5 py-2 font-medium text-[var(--accent-foreground)] disabled:opacity-50"
        >
          {t("send")}
        </button>
      </form>

      <div className="mt-3">
        <PrivacyNotice />
      </div>
    </section>
  );
}
