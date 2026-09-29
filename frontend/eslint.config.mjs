import nextPlugin from "@next/eslint-plugin-next";
import reactPlugin from "eslint-plugin-react";
import reactHooksPlugin from "eslint-plugin-react-hooks";
import tseslint from "typescript-eslint";

// Configuração flat nativa (ESLint 9), sem o shim `FlatCompat`: os plugins do
// Next.js já publicam presets flat próprios nesta versão, e usá-los
// diretamente evita a instabilidade do validador de config legado do
// `@eslint/eslintrc` com plugins que se auto-referenciam (comum em presets
// flat modernos).
export default tseslint.config(
  {
    ignores: [
      ".next/**",
      "node_modules/**",
      "playwright-report/**",
      "test-results/**",
      "next-env.d.ts",
    ],
  },
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{js,jsx,ts,tsx}"],
    plugins: {
      react: reactPlugin,
      "react-hooks": reactHooksPlugin,
      "@next/next": nextPlugin,
    },
    rules: {
      ...reactPlugin.configs.flat.recommended.rules,
      ...reactPlugin.configs.flat["jsx-runtime"].rules,
      ...reactHooksPlugin.configs.flat.recommended.rules,
      ...nextPlugin.configs["core-web-vitals"].rules,
    },
    languageOptions: {
      ...reactPlugin.configs.flat.recommended.languageOptions,
    },
    settings: {
      react: { version: "detect" },
    },
  },
  {
    // Testes: relaxa "no-explicit-any" pontualmente usado em dublês/fakes.
    files: ["tests/**/*.{ts,tsx}"],
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
    },
  },
);
