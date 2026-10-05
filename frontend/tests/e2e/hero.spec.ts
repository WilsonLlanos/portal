import { expect, test } from "@playwright/test";
import { expectNoSeriousAccessibilityViolations } from "./utils/axe";

// T023 (Acceptance Scenario 1 da US1). Roda em mobile e desktop via os
// projetos configurados em playwright.config.ts (T022a).
test.describe("Hero", () => {
  test("mostra foto, nome, título, frase, botão do CV e contatos sem rolagem", async ({ page }) => {
    await page.goto("/pt-BR");

    const hero = page.locator("#hero");
    await expect(hero.getByRole("img")).toBeVisible();
    await expect(hero.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(hero.getByRole("link", { name: /baixar cv/i })).toBeVisible();
    await expect(hero.getByRole("link", { name: "WhatsApp" })).toBeVisible();
    await expect(hero.getByRole("link", { name: /falar comigo/i })).toHaveCount(0);

    // "Sem rolagem": o hero preenche a viewport inicial (min-h-[100svh]).
    const box = await hero.boundingBox();
    const viewport = page.viewportSize();
    expect(box).not.toBeNull();
    expect(viewport).not.toBeNull();
    if (box && viewport) {
      expect(box.y).toBeLessThan(viewport.height);
    }

    await expectNoSeriousAccessibilityViolations(page);
  });

  test("Baixar CV aponta para o PDF do idioma atual", async ({ page }) => {
    await page.goto("/pt-BR");
    const link = page.getByRole("link", { name: /baixar cv/i });
    await expect(link).toHaveAttribute("href", "/cv/cv-pt-BR.pdf");
  });

});
