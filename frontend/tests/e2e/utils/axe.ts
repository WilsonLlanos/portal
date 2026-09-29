import AxeBuilder from "@axe-core/playwright";
import type { Page } from "@playwright/test";
import { expect } from "@playwright/test";

/**
 * T022b: checagem reutilizável de acessibilidade (FR-011) para qualquer
 * spec de E2E. Falha o teste se houver violações de "critical" ou "serious".
 * Violações menores (menor prioridade) são reportadas mas não quebram o teste,
 * para não travar o pipeline por detalhes cosméticos.
 */
export async function expectNoSeriousAccessibilityViolations(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();

  const serious = results.violations.filter(
    (v) => v.impact === "critical" || v.impact === "serious",
  );

  if (serious.length > 0) {
    console.warn(
      "Violações de acessibilidade (critical/serious):",
      serious.map((v) => `${v.id}: ${v.help}`).join("\n"),
    );
  }

  expect(serious, "violações críticas/sérias de acessibilidade (axe)").toEqual([]);
}
