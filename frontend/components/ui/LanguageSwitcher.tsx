"use client";

import { useLocale, useTranslations } from "next-intl";
import { routing } from "@/i18n/routing";
import { usePathname, useRouter } from "@/i18n/navigation";

/**
 * T059: seletor de idioma (FR-008). Troca o locale mantendo a rota atual;
 * a persistência entre navegações vem do próprio locale estar na URL.
 */
export function LanguageSwitcher() {
  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();
  const t = useTranslations("language");

  return (
    <label className="flex items-center gap-2 text-sm">
      <span className="sr-only">{t("label")}</span>
      <select
        value={locale}
        onChange={(event) => router.replace(pathname, { locale: event.target.value })}
        className="rounded-md border border-[var(--border)] bg-[var(--card)] px-2 py-1"
        aria-label={t("label")}
      >
        {routing.locales.map((loc) => (
          <option key={loc} value={loc}>
            {loc === "pt-BR" ? "PT-BR" : "EN"}
          </option>
        ))}
      </select>
    </label>
  );
}
