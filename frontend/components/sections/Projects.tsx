import { getTranslations } from "next-intl/server";
import { AskAiButton } from "@/components/chat/AskAiButton";
import { getProjects } from "@/lib/content/loader";
import type { Locale } from "@/lib/content/schema";

/**
 * T032: projetos em cards (FR-004): selo de contexto (pessoal, desafio
 * técnico, uso no trabalho), descrição, tecnologias, link do GitHub e o botão
 * "Pergunte à IA", que abre o chat para os detalhes do projeto.
 */
export async function Projects({ locale }: { locale: Locale }) {
  const items = getProjects(locale);
  const t = await getTranslations({ locale, namespace: "projects" });

  return (
    <section id="projects" className="section-block px-6 py-8 md:px-10 md:py-10">
      <h2 className="text-2xl font-semibold sm:text-3xl">{t("title")}</h2>
      <div className="mt-8 grid gap-6 md:grid-cols-2">
        {items.map((project) => (
          <article
            key={project.id}
            className="flex flex-col rounded-2xl border border-[var(--border)] bg-[var(--background)] p-6"
          >
            <p className="text-xs font-medium text-[var(--muted-foreground)]">{project.context}</p>
            <h3 className="mt-1 text-lg font-medium">{project.name}</h3>
            <p className="mt-2 text-[var(--muted-foreground)]">{project.description}</p>
            <ul className="mt-4 flex flex-wrap gap-2">
              {project.technologies.map((tech) => (
                <li
                  key={tech}
                  className="rounded-full border border-[var(--border)] px-3 py-1 text-xs"
                >
                  {tech}
                </li>
              ))}
            </ul>
            {/* mt-auto: as ações ficam alinhadas na base, mesmo com textos de tamanhos diferentes. */}
            <div className="mt-auto flex flex-wrap items-center gap-x-4 pt-4">
              <a
                href={project.repoUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-3 inline-block text-sm font-medium text-[var(--accent)] hover:underline"
              >
                {t("repoLink")} →
              </a>
              <AskAiButton
                label={t("askAi")}
                ariaLabel={`${t("askAi")}: ${project.name}`}
                question={t("askAiQuestion", { name: project.name })}
              />
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
