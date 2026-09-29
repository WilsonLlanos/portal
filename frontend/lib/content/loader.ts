import type {
  Certification,
  Experience,
  Locale,
  Profile,
  Project,
} from "./schema";
import { LOCALES, isYearMonth } from "./schema";

// Conteúdo estático, importado em build time (SSG) — ver plan.md § Storage.
import certificationsEn from "@/content/en/certifications.json";
import profileEn from "@/content/en/profile.json";
import projectsEn from "@/content/en/projects.json";
import timelineEn from "@/content/en/timeline.json";
import certificationsPtBR from "@/content/pt-BR/certifications.json";
import profilePtBR from "@/content/pt-BR/profile.json";
import projectsPtBR from "@/content/pt-BR/projects.json";
import timelinePtBR from "@/content/pt-BR/timeline.json";

interface RawContent {
  profile: Profile;
  timeline: { items: Experience[] };
  projects: { items: Project[] };
  certifications: { items: Certification[] };
}

const RAW: Record<Locale, RawContent> = {
  "pt-BR": {
    profile: profilePtBR as Profile,
    timeline: timelinePtBR as { items: Experience[] },
    projects: projectsPtBR as { items: Project[] },
    certifications: certificationsPtBR as { items: Certification[] },
  },
  en: {
    profile: profileEn as Profile,
    timeline: timelineEn as { items: Experience[] },
    projects: projectsEn as { items: Project[] },
    certifications: certificationsEn as { items: Certification[] },
  },
};

/**
 * T011: valida que os dois idiomas têm os mesmos itens (mesmos IDs) e que os
 * campos obrigatórios/formatos de data-model.md são respeitados. Lança erro
 * (falha o build) em vez de deixar passar conteúdo incompleto — cobre o edge
 * case "conteúdo do autor em um idioma ainda sem tradução" da spec.
 *
 * Exportada separadamente do carregamento para poder ser testada (T011a)
 * sem depender dos JSONs reais importados acima.
 */
export function validateContentParity(raw: Record<Locale, RawContent>): void {
  const errors: string[] = [];

  for (const locale of LOCALES) {
    const content = raw[locale];
    if (!content) {
      errors.push(`Idioma ausente: ${locale}`);
      continue;
    }
    if (!content.profile?.photo?.alt) {
      errors.push(`${locale}: profile.photo.alt é obrigatório`);
    }
    for (const exp of content.timeline?.items ?? []) {
      if (!isYearMonth(exp.start)) {
        errors.push(`${locale}: timeline ${exp.id} start inválido (${exp.start})`);
      }
      if (exp.end !== null && !isYearMonth(exp.end)) {
        errors.push(`${locale}: timeline ${exp.id} end inválido (${exp.end})`);
      }
      if (exp.end !== null && exp.start > exp.end) {
        errors.push(`${locale}: timeline ${exp.id} start > end`);
      }
    }
    for (const project of content.projects?.items ?? []) {
      if (!project.technologies || project.technologies.length < 1) {
        errors.push(`${locale}: project ${project.id} precisa de ao menos 1 tecnologia`);
      }
    }
  }

  // Paridade de IDs entre idiomas (o edge case central: nada pode existir só
  // em um idioma).
  const [first, ...rest] = LOCALES;
  const idsOf = (content: RawContent, key: "timeline" | "projects" | "certifications") =>
    new Set((content[key]?.items ?? []).map((item) => item.id));

  for (const key of ["timeline", "projects", "certifications"] as const) {
    const baseIds = raw[first] ? idsOf(raw[first], key) : new Set<string>();
    for (const locale of rest) {
      const content = raw[locale];
      if (!content) continue;
      const otherIds = idsOf(content, key);
      for (const id of baseIds) {
        if (!otherIds.has(id)) {
          errors.push(`${key} "${id}" existe em ${first} mas não em ${locale}`);
        }
      }
      for (const id of otherIds) {
        if (!baseIds.has(id)) {
          errors.push(`${key} "${id}" existe em ${locale} mas não em ${first}`);
        }
      }
    }
  }

  if (errors.length > 0) {
    throw new Error(
      `Conteúdo inconsistente entre idiomas:\n- ${errors.join("\n- ")}`,
    );
  }
}

// Roda uma vez, em build/import time — falha cedo (fail-fast) em vez de
// deixar a inconsistência chegar ao visitante.
validateContentParity(RAW);

export function getProfile(locale: Locale): Profile {
  return RAW[locale].profile;
}

export function getTimeline(locale: Locale): Experience[] {
  // Ordenação cronológica decrescente (mais recente primeiro), conforme
  // data-model.md. Itens em andamento (end = null) vêm primeiro.
  return [...RAW[locale].timeline.items].sort((a, b) => {
    const aKey = a.end ?? "9999-99";
    const bKey = b.end ?? "9999-99";
    return bKey.localeCompare(aKey) || b.start.localeCompare(a.start);
  });
}

export function getProjects(locale: Locale): Project[] {
  return RAW[locale].projects.items;
}

export function getCertifications(locale: Locale): Certification[] {
  return RAW[locale].certifications.items;
}
