import { LanguageSwitcher } from "./LanguageSwitcher";
import { ThemeToggle } from "./ThemeToggle";

/** Barra fixa simples com os controles de idioma e tema (FR-008, FR-009). */
export function Header() {
  return (
    <header className="sticky top-0 z-40 flex justify-end gap-3 border-b border-[var(--border)] bg-[var(--background)]/80 px-6 py-3 backdrop-blur">
      <LanguageSwitcher />
      <ThemeToggle />
    </header>
  );
}
