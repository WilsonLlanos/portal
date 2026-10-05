import { expect, test } from "@playwright/test";
import { expectNoSeriousAccessibilityViolations } from "./utils/axe";

// Botão "Pergunte à IA" da trajetória: leva ao chat e envia a pergunta pronta.
// O backend é simulado com page.route, então o teste não depende de chaves de API.
test("Pergunte à IA envia a pergunta do cargo para o chat", async ({ page }) => {
  let sentBody: { message?: string; lang?: string } | null = null;

  await page.route("**/api/chat", async (route) => {
    sentBody = route.request().postDataJSON();
    await route.fulfill({
      status: 200,
      headers: { "content-type": "text/event-stream" },
      body:
        'event: token\ndata: {"text": "Resposta simulada sobre o cargo."}\n\n' +
        'event: done\ndata: {"outcome": "answered", "suggestions": []}\n\n',
    });
  });

  await page.goto("/pt-BR");
  // Acessibilidade conferida com a página parada no topo: depois do clique, a
  // página rola até o chat e os blocos que saem por cima ficam semi-transparentes
  // de propósito (estado de transição, não conteúdo para leitura).
  await expectNoSeriousAccessibilityViolations(page);

  await page
    .locator("#timeline")
    .getByRole("button", { name: /Pergunte à IA: Desenvolvedor de Sistemas/ })
    .click();

  const chat = page.locator("#chat");
  await expect(chat).toBeInViewport();
  await expect(chat).toContainText(
    "O que o Wilson fez como Desenvolvedor de Sistemas na EISA - Empresa Interagrícola?",
  );
  await expect(chat).toContainText("Resposta simulada sobre o cargo.");
  expect(sentBody).toMatchObject({ lang: "pt-BR" });
});
