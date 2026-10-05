import { getTranslations } from "next-intl/server";
import { getCertifications } from "@/lib/content/loader";
import type { Locale } from "@/lib/content/schema";

/** T033: lista de certificações (FR-005). */
export async function Certifications({ locale }: { locale: Locale }) {
  const items = getCertifications(locale);
  const t = await getTranslations({ locale, namespace: "certifications" });

  return (
    <section id="certifications" className="mx-auto max-w-3xl px-6 py-8 md:py-12">
      <h2 className="text-2xl font-semibold sm:text-3xl">{t("title")}</h2>
      <ul className="mt-8 space-y-4">
        {items.map((cert) => (
          <li
            key={cert.id}
            className="flex flex-col justify-between gap-1 border-b border-[var(--border)] pb-4 sm:flex-row sm:items-center"
          >
            <div>
              <p className="font-medium">{cert.name}</p>
              <p className="text-sm text-[var(--muted-foreground)]">
                {cert.issuer} · {cert.date}
              </p>
            </div>
            {cert.verifyUrl && (
              <a
                href={cert.verifyUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-medium text-[var(--accent)] hover:underline"
              >
                {t("verifyLink")} →
              </a>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
