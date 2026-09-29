import { getTranslations } from "next-intl/server";
import { getProjects } from "@/lib/content/loader";
import type { Locale } from "@/lib/content/schema";

/** T032: projetos em cards com descrição, tecnologias e link do GitHub (FR-004). */
export async function Projects({ locale }: { locale: Locale }) {
  const items = getProjects(locale);
  const t = await getTranslations({ locale, namespace: "projects" });

  return (
    <section id="projects" className="mx-auto max-w-5xl px-6 py-16">
      <h2 className="text-2xl font-semibold sm:text-3xl">{t("title")}</h2>
      <div className="mt-8 grid gap-6 sm:grid-cols-2">
        {items.map((project) => (
          <article
            key={project.id}
            className="rounded-2xl border border-[var(--border)] bg-[var(--card)] p-6"
          >
            <h3 className="text-lg font-medium">{project.name}</h3>
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
            <a
              href={project.repoUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-block font-medium text-[var(--accent)] hover:underline"
            >
              {t("repoLink")} →
            </a>
          </article>
        ))}
      </div>
    </section>
  );
}
