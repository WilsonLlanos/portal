import Image from "next/image";
import { getTranslations } from "next-intl/server";
import { getProfile } from "@/lib/content/loader";
import type { Locale } from "@/lib/content/schema";

/**
 * T024: hero — foto, nome, título, frase de posicionamento e os botões
 * "Baixar CV"/"Falar comigo" (FR-001), tudo visível sem rolagem (SC-001).
 * Layout dividido no desktop, empilhado no celular (brief.md § 4).
 */
export async function Hero({ locale }: { locale: Locale }) {
  const profile = getProfile(locale);
  const t = await getTranslations({ locale, namespace: "hero" });

  return (
    <section
      id="hero"
      className="flex min-h-[calc(100svh-4rem)] flex-col-reverse items-center justify-center gap-8 px-6 py-12 md:flex-row md:gap-16 md:px-16"
    >
      <div className="max-w-xl text-center md:text-left">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
          {profile.name}
        </h1>
        <p className="mt-2 text-lg text-[var(--muted-foreground)] sm:text-xl">
          {profile.headline}
        </p>
        <p className="mt-4 text-base sm:text-lg">{profile.tagline}</p>

        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center md:justify-start">
          {/* T025: CV real do idioma atual (frontend/public/cv/) */}
          <a
            href={`/cv/cv-${locale}.pdf`}
            download
            className="rounded-full bg-[var(--accent)] px-6 py-3 text-center font-medium text-[var(--accent-foreground)] transition-transform hover:scale-105"
          >
            {t("downloadCv")}
          </a>
          {/* T026: leva à seção de contato (US5) */}
          <a
            href="#contact"
            className="rounded-full border border-[var(--border)] px-6 py-3 text-center font-medium transition-colors hover:border-[var(--accent)]"
          >
            {t("talkToMe")}
          </a>
        </div>
      </div>

      {/* Foto com brilho de acento atrás no desktop; sem brilho no celular
          (brief.md § 4), para não poluir a tela inicial em telas pequenas. */}
      <div className="relative shrink-0">
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
    </section>
  );
}
