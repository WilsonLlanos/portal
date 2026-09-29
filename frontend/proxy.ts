import createMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

// Next.js 16 renomeou o arquivo de "middleware.ts" para "proxy.ts" (a API é a
// mesma: export default + config.matcher); next-intl/middleware continua
// funcionando normalmente aqui.
export default createMiddleware(routing);

export const config = {
  // Aplica a todas as rotas exceto arquivos estáticos, imagens e API
  // (o backend é chamado via rewrite em /api/*, não precisa de locale).
  matcher: ["/((?!api|_next|.*\\..*).*)"],
};
