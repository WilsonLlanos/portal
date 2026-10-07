import { expect, test } from "@playwright/test";

// T058 (US4): idioma e tema persistem, e o tema inicial segue o sistema.
test.describe("Idioma e tema", () => {
  test("trocar idioma muda o texto e a navegação seguinte mantém a escolha", async ({ page }) => {
    await page.goto("/pt-BR");
    await expect(page.locator("#hero")).toContainText(/Baixar CV/i);

    await page.getByLabel(/idioma|language/i).selectOption("en");
    await expect(page).toHaveURL(/\/en$/);
    await expect(page.locator("#hero")).toContainText(/Download CV/i);

    await page.getByRole("link", { name: /view on github/i }).first().waitFor();
    await expect(page).toHaveURL(/\/en$/);
  });

  test("tema inicial segue a preferência do sistema (escuro)", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "dark" });
    await page.goto("/pt-BR");
    const html = page.locator("html");
    await expect(html).not.toHaveAttribute("data-theme", "light");
  });

  test("alternar o tema manualmente mantém a escolha ao navegar", async ({ page }) => {
    await page.goto("/pt-BR");
    await page.getByRole("button", { name: /alternar tema/i }).click();
    const themeAfterToggle = await page.locator("html").getAttribute("data-theme");

    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("data-theme", themeAfterToggle ?? "");
  });
});
