import { expect, test } from "@playwright/test";
import { expectNoSeriousAccessibilityViolations } from "./utils/axe";

// T029: resumo, linha do tempo, projetos e certificações (US2).
test("resumo, trajetória, projetos e certificações renderizam com o conteúdo", async ({ page }) => {
  await page.goto("/pt-BR");

  await expect(page.locator("#summary")).toContainText(/./);
  await expect(page.locator("#timeline li").first()).toBeVisible();

  // Trajetória: os três cargos na EISA, numa janela rolável e focável por teclado.
  const timeline = page.locator("#timeline");
  for (const role of ["Desenvolvedor de Sistemas", "Analista Programador", "Analista de Suporte"]) {
    await expect(timeline.getByRole("heading", { name: new RegExp(role) })).toHaveCount(1);
  }
  const scrollWindow = timeline.getByRole("region");
  await expect(scrollWindow).toHaveAttribute("tabindex", "0");
  const isScrollable = await scrollWindow.evaluate((el) => el.scrollHeight > el.clientHeight);
  expect(isScrollable).toBe(true);

  // Efeito de cilindro ativo onde há suporte a scroll-driven animations (Chromium).
  const animationName = await timeline
    .locator("li.timeline-cylinder-item")
    .first()
    .evaluate((el) => getComputedStyle(el).animationName);
  expect(animationName).toBe("timeline-cylinder");

  const firstProjectLink = page.locator("#projects a", { hasText: "Ver repositório" }).first();
  await expect(firstProjectLink).toHaveAttribute("href", /^https:\/\/github\.com\//);

  await expect(page.locator("#certifications li").first()).toBeVisible();

  await expectNoSeriousAccessibilityViolations(page);
});
