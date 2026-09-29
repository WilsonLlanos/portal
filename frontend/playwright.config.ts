import { defineConfig, devices } from "@playwright/test";

// T022a: dois projetos (mobile e desktop) para que todo teste E2E rode nos
// dois formatos automaticamente, sem precisar fixar viewport em cada spec.
export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  reporter: "list",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://127.0.0.1:3000",
    trace: "on-first-retry",
  },
  webServer: process.env.E2E_BASE_URL
    ? undefined
    : {
        command: "npm run build && npm run start",
        url: "http://127.0.0.1:3000",
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      },
  projects: [
    {
      name: "mobile",
      use: { ...devices["Pixel 5"] }, // ~393x851, representa o uso mobile-first (FR-010)
    },
    {
      name: "desktop",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 800 } },
    },
  ],
});
