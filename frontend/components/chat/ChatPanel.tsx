"use client";

import { useLocale, useTranslations } from "next-intl";
import { useEffect, useRef, useState } from "react";
import { ChatError, ChatSuggestions, PrivacyNotice } from "./ChatNotices";
import { useChatSession } from "./useChatSession";

/** Pergunta pronta de um botão "Pergunte à IA"; o id distingue cliques repetidos. */
export type PendingQuestion = { id: number; question: string };

/**
 * T055: chat (US3) como widget fixo no canto da tela, independente das seções.
 * Aberto pelo ChatLauncher, que carrega este componente sob demanda.
 * No celular o painel ocupa a tela inteira; no desktop, um cartão no canto.
 */
export function ChatPanel({
  open,
  onClose,
  pending,
  onPendingHandled,
  contactHref,
  cvHref,
}: {
  open: boolean;
  onClose: () => void;
  pending: PendingQuestion | null;
  onPendingHandled: () => void;
  contactHref: string;
  cvHref: string;
}) {
  const locale = useLocale();
  const t = useTranslations("chat");
  const { messages, isStreaming, error, suggestions, send } = useChatSession(locale);
  const [draft, setDraft] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const handledId = useRef(0);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const text = draft.trim();
    if (!text || isStreaming) return;
    setDraft("");
    void send(text);
  };

  // Perguntas prontas vindas dos botões "Pergunte à IA" da trajetória. O ref
  // evita reenviar a mesma pergunta se o efeito rodar de novo (Strict Mode).
  useEffect(() => {
    if (!pending || pending.id === handledId.current) return;
    handledId.current = pending.id;
    onPendingHandled();
    if (!isStreaming) void send(pending.question);
  }, [pending, isStreaming, send, onPendingHandled]);

  // Foco no campo ao abrir; Esc fecha.
  useEffect(() => {
    if (!open) return;
    inputRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  // Mantém a última mensagem visível durante o streaming.
  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages]);

  // Fechado, o painel continua montado (sem renderizar nada) para manter a conversa.
  if (!open) return null;

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
          onClick={onClose}
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
        <div onClick={onClose}>
          <ChatSuggestions items={suggestions} contactHref={contactHref} cvHref={cvHref} />
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
