import { expect, test } from "@playwright/test";

// T062 (US5): os três links de contato levam ao destino correto.
test("os links de contato apontam para LinkedIn, GitHub e e-mail", async ({ page }) => {
  await page.goto("/pt-BR");
  const contact = page.locator("#contact");

  await expect(contact.getByRole("link", { name: "LinkedIn" })).toHaveAttribute(
    "href",
    /linkedin\.com/,
  );
  await expect(contact.getByRole("link", { name: "GitHub" })).toHaveAttribute(
    "href",
    /github\.com/,
  );
  await expect(contact.getByRole("link", { name: "E-mail" })).toHaveAttribute(
    "href",
    /^mailto:/,
  );
});
