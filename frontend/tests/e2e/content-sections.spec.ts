import { expect, test } from "@playwright/test";
import { expectNoSeriousAccessibilityViolations } from "./utils/axe";

// T029: resumo, linha do tempo, projetos e certificações (US2).
test("resumo, trajetória, projetos e certificações renderizam com o conteúdo", async ({ page }) => {
  await page.goto("/pt-BR");

  await expect(page.locator("#summary")).toContainText(/./);
  await expect(page.locator("#timeline li").first()).toBeVisible();

  const firstProjectLink = page.locator("#projects a", { hasText: "Ver repositório" }).first();
  await expect(firstProjectLink).toHaveAttribute("href", /^https:\/\/github\.com\//);

  await expect(page.locator("#certifications li").first()).toBeVisible();

  await expectNoSeriousAccessibilityViolations(page);
});
