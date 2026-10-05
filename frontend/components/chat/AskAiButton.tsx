"use client";

/** Evento que o ChatPanel escuta para enviar uma pergunta pronta. */
export const ASK_AI_EVENT = "portal:ask-ai";

/**
 * Botão "Pergunte à IA" de cada cargo da trajetória: leva o visitante ao chat
 * e envia a pergunta, mostrando o RAG respondendo sobre o próprio currículo.
 * Comunicação por CustomEvent porque a Timeline é server component e o chat
 * guarda o próprio estado (useChatSession).
 */
export function AskAiButton({
  question,
  label,
  ariaLabel,
}: {
  question: string;
  label: string;
  ariaLabel: string;
}) {
  const handleClick = () => {
    window.dispatchEvent(new CustomEvent<string>(ASK_AI_EVENT, { detail: question }));
    document.getElementById("chat")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      aria-label={ariaLabel}
      className="mt-3 rounded-full border border-[var(--accent)] px-3 py-1 text-xs font-medium text-[var(--accent)] transition-colors hover:bg-[var(--accent)] hover:text-[var(--accent-foreground)]"
    >
      ✨ {label}
    </button>
  );
}
