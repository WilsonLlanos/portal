import { expect, test } from "@playwright/test";
import { expectNoSeriousAccessibilityViolations } from "./utils/axe";

// Chat como widget fixo: abre pelo botão flutuante, tem um único campo de texto
// e uma saudação no lugar da antiga área vazia (que parecia um segundo campo).
test("chat flutuante abre, mostra saudação, tem um só campo e fecha com Esc", async ({ page }) => {
  await page.goto("/pt-BR");

  const launcher = page.getByRole("button", { name: /Pergunte à IA sobre minha carreira/ });
  await expect(launcher).toBeVisible();
  await expect(page.locator("#chat")).toHaveCount(0); // fechado por padrão

  await launcher.click();
  const chat = page.getByRole("dialog", { name: /Converse sobre minha carreira/ });
  await expect(chat).toBeVisible();
  await expect(chat).toContainText("Sou o assistente de IA do Wilson");
  await expect(chat.getByRole("textbox")).toHaveCount(1);
  await expect(chat.getByRole("textbox")).toBeFocused();

  await expectNoSeriousAccessibilityViolations(page);

  await page.keyboard.press("Escape");
  await expect(page.locator("#chat")).toHaveCount(0);
  await expect(launcher).toBeVisible();
});
