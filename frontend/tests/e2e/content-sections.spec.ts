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
  // O curso de ML aparece como o "start" na IA, com data única (só a conclusão).
  await expect(timeline).toContainText("Pipeline ETL e Machine Learning com Apache Spark");
  // Botão para o CV logo abaixo da trajetória.
  await expect(timeline.getByRole("link", { name: /Ver detalhes no currículo/ })).toHaveAttribute(
    "href",
    "/cv/cv-pt-BR.pdf",
  );

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

  // Projetos: três cards reais, cada um com link do GitHub e "Pergunte à IA".
  const projects = page.locator("#projects article");
  await expect(projects).toHaveCount(3);
  const repoLinks = page.locator("#projects a", { hasText: "Ver no GitHub" });
  await expect(repoLinks).toHaveCount(3);
  await expect(repoLinks.first()).toHaveAttribute("href", /^https:\/\/github\.com\/WilsonLlanos\//);
  await expect(page.locator("#projects").getByRole("button", { name: /Pergunte à IA/ })).toHaveCount(3);
  await expect(page.locator("#projects")).toContainText("Desafio técnico (case Getnet)");

  await expect(page.locator("#certifications li").first()).toBeVisible();
  // Mais recente primeiro: a certificação da Microsoft vem antes da de ML.
  await expect(page.locator("#certifications li").first()).toContainText("Microsoft");

  // Blocos com profundidade: encaixe suave na rolagem e animação de saída (Chromium).
  const snapType = await page.evaluate(() => getComputedStyle(document.documentElement).scrollSnapType);
  expect(snapType).toContain("y");
  const sectionAnimation = await page
    .locator("#summary")
    .evaluate((el) => getComputedStyle(el).animationName);
  expect(sectionAnimation).toBe("section-exit");

  await expectNoSeriousAccessibilityViolations(page);
});
