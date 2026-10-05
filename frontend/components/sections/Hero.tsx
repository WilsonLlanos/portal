import Image from "next/image";
import { getTranslations } from "next-intl/server";
import { ContactLinks } from "@/components/ui/ContactLinks";
import { getProfile } from "@/lib/content/loader";
import type { Locale } from "@/lib/content/schema";

/**
 * T024: hero — foto, nome, título, frase de posicionamento, botão "Baixar CV"
 * e os ícones de contato logo abaixo da foto (FR-001, FR-007), tudo visível
 * sem rolagem (SC-001). Layout dividido no desktop, empilhado no celular
 * (brief.md § 4).
 */
export async function Hero({ locale }: { locale: Locale }) {
  const profile = getProfile(locale);
  const t = await getTranslations({ locale, namespace: "hero" });

  return (
    <section
      id="hero"
      className="section-block flex min-h-[calc(100svh-9rem)] flex-col-reverse items-center justify-center gap-8 px-6 py-10 md:flex-row md:gap-16 md:px-16"
    >
      <div className="max-w-xl text-center md:text-left">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
          {profile.name}
        </h1>
        <p className="mt-2 text-lg text-[var(--muted-foreground)] sm:text-xl">
          {profile.headline}
        </p>
        <p className="mt-4 text-base sm:text-lg">{profile.tagline}</p>

        <div className="mt-8 flex justify-center md:justify-start">
          {/* T025: CV real do idioma atual (frontend/public/cv/) */}
          <a
            href={`/cv/cv-${locale}.pdf`}
            download
            className="rounded-full bg-[var(--accent)] px-6 py-3 text-center font-medium text-[var(--accent-foreground)] transition-transform hover:scale-105"
          >
            {t("downloadCv")}
          </a>
        </div>
      </div>

      {/* Foto com brilho de acento atrás no desktop; sem brilho no celular
          (brief.md § 4), para não poluir a tela inicial em telas pequenas.
          Os contatos ficam logo abaixo da foto. */}
      <div className="flex shrink-0 flex-col items-center gap-4">
        <div className="relative">
          <div
            aria-hidden
            className="absolute inset-0 -z-10 hidden rounded-full bg-[var(--accent)] opacity-20 blur-3xl md:block"
          />
          <Image
            src={profile.photo.src}
            alt={profile.photo.alt}
            width={288}
            height={288}
            priority
            className="h-48 w-48 rounded-3xl border border-[var(--border)] object-cover shadow-xl sm:h-64 sm:w-64 md:h-72 md:w-72"
          />
        </div>
        <ContactLinks locale={locale} />
      </div>
    </section>
  );
}
