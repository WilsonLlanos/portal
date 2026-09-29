"use client";

import { useTranslations } from "next-intl";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

/**
 * T060: alternador de tema claro/escuro (FR-009). `mounted` evita
 * mismatch de hidratação, já que o tema inicial depende do sistema/localStorage
 * (só disponíveis no cliente).
 */
export function ThemeToggle() {
  const { theme, setTheme, systemTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const t = useTranslations("theme");

  useEffect(() => {
    // Padrão recomendado pelo next-themes para evitar mismatch de hidratação:
    // o tema real só é conhecido no cliente (localStorage/preferência do
    // sistema), então o primeiro render assume "não montado".
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
  }, []);

  if (!mounted) {
    // Placeholder do mesmo tamanho, para não pular o layout (CLS).
    return <div className="h-9 w-9" aria-hidden />;
  }

  const current = theme === "system" ? systemTheme : theme;
  const next = current === "dark" ? "light" : "dark";

  return (
    <button
      type="button"
      onClick={() => setTheme(next)}
      className="flex h-9 w-9 items-center justify-center rounded-full border border-[var(--border)]"
      aria-label={t("toggle")}
      title={t("toggle")}
    >
      {current === "dark" ? "🌙" : "☀️"}
    </button>
  );
}
