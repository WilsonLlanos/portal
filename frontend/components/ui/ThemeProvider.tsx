"use client";

import { ThemeProvider as NextThemesProvider } from "next-themes";
import type { ReactNode } from "react";

/**
 * FR-009: tema claro/escuro, com padrão = preferência do sistema e troca
 * manual persistida (next-themes usa localStorage por padrão — persistência
 * é uma conveniência por visitante, não um dado que precisamos ler de volta).
 * attribute="data-theme" para casar com os seletores de app/globals.css.
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
  return (
    <NextThemesProvider attribute="data-theme" defaultTheme="system" enableSystem>
      {children}
    </NextThemesProvider>
  );
}
