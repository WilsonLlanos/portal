import { getTranslations } from "next-intl/server";
import { getProfile } from "@/lib/content/loader";
import type { Locale } from "@/lib/content/schema";
import { ContactIcon } from "./ContactIcons";

/**
 * Contatos (FR-007) como ícones com nome acessível: LinkedIn, GitHub, e-mail e
 * WhatsApp. Exibidos logo abaixo da foto, na tela inicial.
 */
export async function ContactLinks({ locale }: { locale: Locale }) {
  const profile = getProfile(locale);
  const t = await getTranslations({ locale, namespace: "contact" });

  const contacts = [
    { name: "linkedin", href: profile.links.linkedin, label: t("linkedin") },
    { name: "github", href: profile.links.github, label: t("github") },
    { name: "email", href: `mailto:${profile.links.email}`, label: t("email") },
    { name: "whatsapp", href: profile.links.whatsapp, label: t("whatsapp") },
  ] as const;

  return (
    <nav id="contact" aria-label={t("title")}>
      <ul className="flex items-center justify-center gap-2">
        {contacts.map((contact) => {
          const external = !contact.href.startsWith("mailto:");
          return (
            <li key={contact.name}>
              <a
                href={contact.href}
                aria-label={contact.label}
                title={contact.label}
                target={external ? "_blank" : undefined}
                rel={external ? "noopener noreferrer" : undefined}
                className="flex h-10 w-10 items-center justify-center rounded-full border border-[var(--border)] text-[var(--muted-foreground)] transition-colors hover:border-[var(--accent)] hover:text-[var(--accent)]"
              >
                <ContactIcon name={contact.name} />
              </a>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
