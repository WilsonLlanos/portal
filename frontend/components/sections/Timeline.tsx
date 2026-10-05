import { getTranslations } from "next-intl/server";
import { AskAiButton } from "@/components/chat/AskAiButton";
import { getTimeline } from "@/lib/content/loader";
import type { Locale } from "@/lib/content/schema";

/**
 * T031: linha do tempo cronológica de experiências profissionais e
 * acadêmicas (FR-003). Ordenação já vem de getTimeline (data-model.md).
 *
 * A lista fica numa janela de altura fixa com rolagem própria; `mask-image`
 * esmaece o texto nas bordas de cima e de baixo. Só CSS: ao chegar ao fim da
 * janela, a rolagem volta para a página (não prende o visitante no celular).
 */
export async function Timeline({ locale }: { locale: Locale }) {
  const items = getTimeline(locale);
  const t = await getTranslations({ locale, namespace: "timeline" });

  return (
    <section id="timeline" className="section-block px-6 py-8 md:px-10 md:py-10">
      <h2 className="text-2xl font-semibold sm:text-3xl">{t("title")}</h2>

      {/* tabIndex/role/aria-label: região rolável precisa ser alcançável por
          teclado (regra "scrollable-region-focusable" do axe, FR-011). */}
      <div
        tabIndex={0}
        role="region"
        aria-label={t("title")}
        className="mt-6 h-[28rem] overflow-y-auto rounded-lg py-10 [mask-image:linear-gradient(to_bottom,transparent,black_15%,black_85%,transparent)] [scrollbar-width:thin] md:h-[32rem]"
      >
        <ol className="ml-2 space-y-8 border-l border-[var(--border)] pl-6">
          {items.map((item) => (
            <li key={item.id} className="timeline-cylinder-item relative">
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
              {item.kind === "professional" && (
                <AskAiButton
                  label={t("askAi")}
                  ariaLabel={`${t("askAi")}: ${item.role}`}
                  question={t("askAiQuestion", {
                    role: item.role,
                    organization: item.organization,
                  })}
                />
              )}
            </li>
          ))}
        </ol>
      </div>

      <p className="mt-3 text-center text-sm text-[var(--muted-foreground)]">
        {t("scrollHint")}
      </p>
    </section>
  );
}
