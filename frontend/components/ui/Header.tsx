import { getTranslations } from "next-intl/server";
import { getProfile } from "@/lib/content/loader";
import type { Locale } from "@/lib/content/schema";
import { ContactIcon } from "./ContactIcons";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { ThemeToggle } from "./ThemeToggle";

/**
 * Barra fixa: contatos (FR-007) à esquerda, idioma e tema (FR-008, FR-009) à
 * direita. Os contatos ficam sempre à mão, em vez de numa seção no fim da página.
 */
export async function Header({ locale }: { locale: Locale }) {
  const profile = getProfile(locale);
  const t = await getTranslations({ locale, namespace: "contact" });

  const contacts = [
    { name: "linkedin", href: profile.links.linkedin, label: t("linkedin") },
    { name: "github", href: profile.links.github, label: t("github") },
    { name: "email", href: `mailto:${profile.links.email}`, label: t("email") },
    { name: "whatsapp", href: profile.links.whatsapp, label: t("whatsapp") },
  ] as const;

  return (
    <header
      id="contact"
      className="sticky top-0 z-40 flex items-center justify-between gap-3 border-b border-[var(--border)] bg-[var(--background)]/80 px-4 py-3 backdrop-blur sm:px-6"
    >
      <nav aria-label={t("title")}>
        <ul className="flex items-center gap-1">
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
                  className="flex h-9 w-9 items-center justify-center rounded-full text-[var(--muted-foreground)] transition-colors hover:bg-[var(--card)] hover:text-[var(--accent)]"
                >
                  <ContactIcon name={contact.name} />
                </a>
              </li>
            );
          })}
        </ul>
      </nav>
      <div className="flex items-center gap-3">
        <LanguageSwitcher />
        <ThemeToggle />
      </div>
    </header>
  );
}
