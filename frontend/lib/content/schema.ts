/**
 * Esquema de conteúdo (T008), espelhando specs/001-portfolio-portal/data-model.md § 1.
 * Cada idioma (pt-BR, en) tem os mesmos arquivos e os mesmos IDs — é o que o
 * loader (loader.ts) valida para cobrir o edge case "idioma sem tradução".
 */

export interface Profile {
  name: string;
  headline: string;
  tagline: string;
  summary: string;
  photo: {
    src: string;
    /** Texto alternativo obrigatório (acessibilidade, FR-011). */
    alt: string;
  };
  links: {
    linkedin: string;
    github: string;
    email: string;
    /** Telefone no formato internacional para exibição, ex.: "+55 11 97522-5763". */
    phone: string;
    /** Link wa.me com mensagem inicial pronta (escolha do autor publicar o número). */
    whatsapp: string;
  };
}

export interface Experience {
  id: string;
  kind: "professional" | "academic";
  organization: string;
  role: string;
  /** Formato YYYY-MM. */
  start: string;
  /** Formato YYYY-MM, ou null se em andamento. */
  end: string | null;
  description: string;
  highlights: string[];
}

export interface Project {
  id: string;
  name: string;
  description: string;
  /** Ao menos 1 tecnologia. */
  technologies: string[];
  repoUrl: string;
  demoUrl: string | null;
}

export interface Certification {
  id: string;
  name: string;
  issuer: string;
  /** Formato YYYY-MM. */
  date: string;
  verifyUrl: string | null;
}

export type Locale = "pt-BR" | "en";
export const LOCALES: Locale[] = ["pt-BR", "en"];
export const DEFAULT_LOCALE: Locale = "pt-BR";

/** Valida `YYYY-MM`. */
export function isYearMonth(value: string): boolean {
  return /^\d{4}-(0[1-9]|1[0-2])$/.test(value);
}
