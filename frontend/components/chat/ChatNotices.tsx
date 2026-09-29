"use client";

import { useTranslations } from "next-intl";
import type { ChatErrorCode } from "./useChatSession";

const ERROR_MESSAGE_KEY: Record<ChatErrorCode, string> = {
  empty_message: "errorGeneric",
  message_too_long: "errorTooLong",
  rate_limited: "errorRateLimited",
  chat_paused: "errorPaused",
  unavailable: "errorGeneric",
};

/**
 * T056: aviso de privacidade (FR-022) e mensagens de limite/pausa/erro
 * (FR-019), sempre com uma alternativa (CV/contato) — o texto já traz isso.
 */
export function PrivacyNotice() {
  const t = useTranslations("chat");
  return (
    <p className="text-xs text-[var(--muted-foreground)]" role="note">
      {t("privacyNotice")}
    </p>
  );
}

export function ChatError({ code }: { code: ChatErrorCode }) {
  const t = useTranslations("chat");
  return (
    <p role="alert" className="rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-600 dark:text-red-400">
      {t(ERROR_MESSAGE_KEY[code])}
    </p>
  );
}

export function ChatSuggestions({ items }: { items: string[] }) {
  const t = useTranslations("chat.suggestions");
  const hrefFor: Record<string, string> = {
    projects: "#projects",
    cv: "#hero",
    contact: "#contact",
  };

  if (items.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 pt-1">
      {items.map((item) => (
        <a
          key={item}
          href={hrefFor[item] ?? "#"}
          className="rounded-full border border-[var(--border)] px-3 py-1 text-xs hover:border-[var(--accent)]"
        >
          {t(item)}
        </a>
      ))}
    </div>
  );
}
