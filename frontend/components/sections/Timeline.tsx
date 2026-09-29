import { getTranslations } from "next-intl/server";
import { getTimeline } from "@/lib/content/loader";
import type { Locale } from "@/lib/content/schema";

/**
 * T031: linha do tempo cronológica de experiências profissionais e
 * acadêmicas (FR-003). Ordenação já vem de getTimeline (data-model.md).
 */
export async function Timeline({ locale }: { locale: Locale }) {
  const items = getTimeline(locale);
  const t = await getTranslations({ locale, namespace: "timeline" });

  return (
    <section id="timeline" className="mx-auto max-w-3xl px-6 py-16">
      <h2 className="text-2xl font-semibold sm:text-3xl">{t("title")}</h2>
      <ol className="mt-8 space-y-8 border-l border-[var(--border)] pl-6">
        {items.map((item) => (
          <li key={item.id} className="relative">
            <span
              aria-hidden
              className="absolute -left-[1.6rem] top-1.5 h-3 w-3 rounded-full bg-[var(--accent)]"
            />
            <p className="text-sm text-[var(--muted-foreground)]">
              {item.start} — {item.end ?? t("present")}
              {" · "}
              {item.kind === "academic" ? "🎓" : "💼"}
            </p>
            <h3 className="mt-1 text-lg font-medium">
              {item.role} · {item.organization}
            </h3>
            <p className="mt-1 text-[var(--muted-foreground)]">{item.description}</p>
            {item.highlights.length > 0 && (
              <ul className="mt-2 list-inside list-disc text-sm text-[var(--muted-foreground)]">
                {item.highlights.map((highlight) => (
                  <li key={highlight}>{highlight}</li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}
