import { getTranslations } from "next-intl/server";
import { getProfile } from "@/lib/content/loader";
import type { Locale } from "@/lib/content/schema";

/**
 * T063: contato por links (LinkedIn, GitHub, e-mail), sem formulário
 * próprio na v1, conforme a clarificação registrada em spec.md (FR-007).
 */
export async function Contact({ locale }: { locale: Locale }) {
  const profile = getProfile(locale);
  const t = await getTranslations({ locale, namespace: "contact" });

  const links = [
    { href: profile.links.linkedin, label: t("linkedin") },
    { href: profile.links.github, label: t("github") },
    { href: `mailto:${profile.links.email}`, label: t("email") },
  ];

  return (
    <section id="contact" className="mx-auto max-w-3xl px-6 py-8 md:py-12 text-center">
      <h2 className="text-2xl font-semibold sm:text-3xl">{t("title")}</h2>
      <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
        {links.map((link) => (
          <a
            key={link.label}
            href={link.href}
            target={link.href.startsWith("mailto:") ? undefined : "_blank"}
            rel={link.href.startsWith("mailto:") ? undefined : "noopener noreferrer"}
            className="w-full rounded-full border border-[var(--border)] px-6 py-3 font-medium transition-colors hover:border-[var(--accent)] sm:w-auto"
          >
            {link.label}
          </a>
        ))}
      </div>
    </section>
  );
}
