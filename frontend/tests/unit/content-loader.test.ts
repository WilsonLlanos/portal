import { describe, expect, it } from "vitest";
import { validateContentParity } from "@/lib/content/loader";
import type { Certification, Experience, Profile, Project } from "@/lib/content/schema";

// T011a: cobre o edge case "conteúdo do autor em um idioma ainda sem
// tradução" — a validação deve falhar (lançar) em vez de deixar passar.

function makeProfile(overrides: Partial<Profile> = {}): Profile {
  return {
    name: "Test",
    headline: "Headline",
    tagline: "Tagline",
    summary: "Summary",
    photo: { src: "/x.png", alt: "alt text" },
    links: { linkedin: "", github: "", email: "", phone: "", whatsapp: "" },
    ...overrides,
  };
}

function baseRaw() {
  return {
    "pt-BR": {
      profile: makeProfile(),
      timeline: { items: [] as Experience[] },
      projects: { items: [] as Project[] },
      certifications: { items: [] as Certification[] },
    },
    en: {
      profile: makeProfile(),
      timeline: { items: [] as Experience[] },
      projects: { items: [] as Project[] },
      certifications: { items: [] as Certification[] },
    },
  };
}

describe("validateContentParity", () => {
  it("aceita conteúdo idêntico e completo nos dois idiomas", () => {
    expect(() => validateContentParity(baseRaw())).not.toThrow();
  });

  it("falha quando falta o alt da foto em um idioma", () => {
    const raw = baseRaw();
    raw.en.profile = makeProfile({ photo: { src: "/x.png", alt: "" } });
    expect(() => validateContentParity(raw)).toThrow(/alt/);
  });

  it("falha quando um projeto existe só em um idioma (sem tradução)", () => {
    const raw = baseRaw();
    raw["pt-BR"].projects.items = [
      {
        id: "only-pt",
        name: "Nome",
        context: "Pessoal",
        description: "Desc",
        technologies: ["Python"],
        repoUrl: "https://example.com",
        demoUrl: null,
      },
    ];
    // en não tem o item "only-pt" — deve falhar.
    expect(() => validateContentParity(raw)).toThrow(/only-pt/);
  });

  it("falha quando uma experiência tem data start posterior a end", () => {
    const raw = baseRaw();
    const exp: Experience = {
      id: "exp-1",
      kind: "professional",
      organization: "Org",
      role: "Role",
      start: "2024-06",
      end: "2024-01",
      description: "",
      highlights: [],
    };
    raw["pt-BR"].timeline.items = [exp];
    raw.en.timeline.items = [exp];
    expect(() => validateContentParity(raw)).toThrow(/start > end/);
  });
});
