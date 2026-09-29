import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Testes unitários (lógica e componentes). Os testes end-to-end ficam no
// Playwright (ver playwright.config.ts) — Vitest não deve tentar rodá-los.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL(".", import.meta.url)),
    },
  },
  test: {
    environment: "jsdom",
    include: ["tests/unit/**/*.test.{ts,tsx}"],
    exclude: ["tests/e2e/**"],
  },
});
