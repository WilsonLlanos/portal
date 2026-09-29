import { defineRouting } from "next-intl/routing";

// pt-BR como alternativa quando o navegador não corresponder a nenhum
// suportado (Assumptions da spec).
export const routing = defineRouting({
  locales: ["pt-BR", "en"],
  defaultLocale: "pt-BR",
  localePrefix: "always",
});

export type AppLocale = (typeof routing.locales)[number];
