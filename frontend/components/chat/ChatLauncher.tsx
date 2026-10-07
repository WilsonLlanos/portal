"use client";

import { useTranslations } from "next-intl";
import dynamic from "next/dynamic";
import { useCallback, useEffect, useRef, useState } from "react";
import { ASK_AI_EVENT } from "./AskAiButton";
import type { PendingQuestion } from "./ChatPanel";

// O painel (e o useChatSession) só é baixado quando o visitante demonstra
// intenção de usar o chat: tira esse JS do carregamento inicial e reduz o
// Total Blocking Time medido pelo Lighthouse (SC-004).
const ChatPanel = dynamic(() => import("./ChatPanel").then((m) => m.ChatPanel), { ssr: false });
const preloadPanel = () => void import("./ChatPanel");

/**
 * Botão flutuante do chat. Carrega o ChatPanel sob demanda e, depois de
 * carregado, mantém o painel montado para preservar a conversa ao fechar.
 */
export function ChatLauncher({ contactHref, cvHref }: { contactHref: string; cvHref: string }) {
  const t = useTranslations("chat");
  const [loaded, setLoaded] = useState(false);
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState<PendingQuestion | null>(null);
  const nextId = useRef(0);

  const openChat = () => {
    setLoaded(true);
    setOpen(true);
  };
  const closeChat = useCallback(() => setOpen(false), []);
  const clearPending = useCallback(() => setPending(null), []);

  // Perguntas prontas vindas dos botões "Pergunte à IA" da trajetória.
  useEffect(() => {
    const onAskAi = (event: Event) => {
      const question = (event as CustomEvent<string>).detail;
      if (!question) return;
      setPending({ id: ++nextId.current, question });
      setLoaded(true);
      setOpen(true);
    };
    window.addEventListener(ASK_AI_EVENT, onAskAi);
    return () => window.removeEventListener(ASK_AI_EVENT, onAskAi);
  }, []);

  return (
    <>
      {!open && (
        <button
          type="button"
          onClick={openChat}
          onPointerEnter={preloadPanel}
          onFocus={preloadPanel}
          className="fixed bottom-4 right-4 z-50 flex items-center gap-2 rounded-full bg-[var(--accent)] px-5 py-3 font-medium text-[var(--accent-foreground)] shadow-lg transition-transform hover:scale-105"
        >
          <span aria-hidden>✨</span>
          {t("launcher")}
        </button>
      )}
      {loaded && (
        <ChatPanel
          open={open}
          onClose={closeChat}
          pending={pending}
          onPendingHandled={clearPending}
          contactHref={contactHref}
          cvHref={cvHref}
        />
      )}
    </>
  );
}
