import { expect, test } from "@playwright/test";

// T062 (US5): contatos como ícones no header fixo (LinkedIn, GitHub, e-mail, WhatsApp).
test("os ícones de contato do header apontam para os destinos certos", async ({ page }) => {
  await page.goto("/pt-BR");
  const header = page.locator("header#contact");

  await expect(header.getByRole("link", { name: "LinkedIn" })).toHaveAttribute(
    "href",
    /linkedin\.com\/in\/wilson-llanos/,
  );
  await expect(header.getByRole("link", { name: "GitHub" })).toHaveAttribute(
    "href",
    /github\.com\/WilsonLlanos/,
  );
  await expect(header.getByRole("link", { name: "E-mail" })).toHaveAttribute(
    "href",
    "mailto:wilson.llanos@outlook.com",
  );
  await expect(header.getByRole("link", { name: "WhatsApp" })).toHaveAttribute(
    "href",
    /^https:\/\/wa\.me\/5511975225763\?text=/,
  );
});
