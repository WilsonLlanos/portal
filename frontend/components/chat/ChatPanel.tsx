"use client";

import { useLocale, useTranslations } from "next-intl";
import { useEffect, useRef, useState } from "react";
import { ASK_AI_EVENT } from "./AskAiButton";
import { ChatError, ChatSuggestions, PrivacyNotice } from "./ChatNotices";
import { useChatSession } from "./useChatSession";

/**
 * T055: chat (US3) como widget fixo no canto da tela, independente das seções:
 * um botão abre o painel, que fica disponível em qualquer ponto da página.
 * No celular o painel ocupa a tela inteira; no desktop, um cartão no canto.
 */
export function ChatPanel() {
  const locale = useLocale();
  const t = useTranslations("chat");
  const { messages, isStreaming, error, suggestions, send } = useChatSession(locale);
  const [draft, setDraft] = useState("");
  const [open, setOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

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
      setOpen(true);
      void send(question);
    };
    window.addEventListener(ASK_AI_EVENT, onAskAi);
    return () => window.removeEventListener(ASK_AI_EVENT, onAskAi);
  }, [isStreaming, send]);

  // Foco no campo ao abrir; Esc fecha.
  useEffect(() => {
    if (!open) return;
    inputRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open]);

  // Mantém a última mensagem visível durante o streaming.
  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages]);

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-4 right-4 z-50 flex items-center gap-2 rounded-full bg-[var(--accent)] px-5 py-3 font-medium text-[var(--accent-foreground)] shadow-lg transition-transform hover:scale-105"
      >
        <span aria-hidden>✨</span>
        {t("launcher")}
      </button>
    );
  }

  return (
    <section
      id="chat"
      role="dialog"
      aria-modal="false"
      aria-label={t("title")}
      className="fixed inset-0 z-50 flex flex-col bg-[var(--card)] sm:inset-auto sm:bottom-4 sm:right-4 sm:h-[34rem] sm:max-h-[calc(100svh-2rem)] sm:w-[24rem] sm:rounded-3xl sm:border sm:border-[var(--border)] sm:shadow-2xl"
    >
      <header className="flex items-center justify-between border-b border-[var(--border)] px-5 py-3">
        <h2 className="font-semibold">{t("title")}</h2>
        <button
          type="button"
          onClick={() => setOpen(false)}
          aria-label={t("close")}
          className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-[var(--background)]"
        >
          ✕
        </button>
      </header>

      <div ref={listRef} className="flex flex-1 flex-col gap-3 overflow-y-auto p-4" aria-live="polite">
        {messages.length === 0 && (
          <p className="self-start rounded-2xl rounded-bl-sm bg-[var(--background)] px-4 py-2 text-sm">
            {t("greeting")}
          </p>
        )}
        {messages.map((message, index) => (
          <div
            key={index}
            className={
              message.role === "user"
                ? "self-end rounded-2xl rounded-br-sm bg-[var(--accent)] px-4 py-2 text-sm text-[var(--accent-foreground)]"
                : "self-start rounded-2xl rounded-bl-sm bg-[var(--background)] px-4 py-2 text-sm"
            }
          >
            {message.content || (isStreaming && index === messages.length - 1 ? "…" : "")}
          </div>
        ))}
        {error && <ChatError code={error.code} />}
        {/* Sugestões levam a seções da página: fecha o painel para mostrá-las. */}
        <div onClick={() => setOpen(false)}>
          <ChatSuggestions items={suggestions} />
        </div>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 border-t border-[var(--border)] px-4 pt-3">
        <label htmlFor="chat-input" className="sr-only">
          {t("placeholder")}
        </label>
        <input
          ref={inputRef}
          id="chat-input"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder={t("placeholder")}
          maxLength={500}
          disabled={isStreaming}
          className="min-w-0 flex-1 rounded-full border border-[var(--border)] bg-[var(--background)] px-4 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={isStreaming || !draft.trim()}
          className="rounded-full bg-[var(--accent)] px-4 py-2 text-sm font-medium text-[var(--accent-foreground)] disabled:opacity-50"
        >
          {t("send")}
        </button>
      </form>

      <div className="px-4 pb-3 pt-2">
        <PrivacyNotice />
      </div>
    </section>
  );
}
