import { getTranslations } from "next-intl/server";
import { getProfile } from "@/lib/content/loader";
import type { Locale } from "@/lib/content/schema";

/** T030: resumo de carreira curto com foco em IA (FR-002). */
export async function Summary({ locale }: { locale: Locale }) {
  const profile = getProfile(locale);
  const t = await getTranslations({ locale, namespace: "summary" });

  return (
    <section id="summary" className="mx-auto max-w-3xl px-6 py-16">
      <h2 className="text-2xl font-semibold sm:text-3xl">{t("title")}</h2>
      <p className="mt-4 text-lg leading-relaxed text-[var(--muted-foreground)]">
        {profile.summary}
      </p>
    </section>
  );
}
