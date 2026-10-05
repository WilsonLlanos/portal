import { expect, test } from "@playwright/test";

// T062 (US5): contatos como ícones logo abaixo da foto (LinkedIn, GitHub, e-mail, WhatsApp).
test("os ícones de contato abaixo da foto apontam para os destinos certos", async ({ page }) => {
  await page.goto("/pt-BR");
  const contacts = page.locator("#hero nav#contact");

  await expect(contacts.getByRole("link", { name: "LinkedIn" })).toHaveAttribute(
    "href",
    /linkedin\.com\/in\/wilson-llanos/,
  );
  await expect(contacts.getByRole("link", { name: "GitHub" })).toHaveAttribute(
    "href",
    /github\.com\/WilsonLlanos/,
  );
  await expect(contacts.getByRole("link", { name: "E-mail" })).toHaveAttribute(
    "href",
    "mailto:wilson.llanos@outlook.com",
  );
  await expect(contacts.getByRole("link", { name: "WhatsApp" })).toHaveAttribute(
    "href",
    /^https:\/\/wa\.me\/5511975225763\?text=/,
  );
});
