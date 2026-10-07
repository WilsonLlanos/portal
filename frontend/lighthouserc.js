/** T066: Lighthouse CI — meta de SC-004 (>90 em desempenho, acessibilidade, SEO). */
module.exports = {
  ci: {
    collect: {
      startServerCommand: "npm run start",
      url: ["http://127.0.0.1:3000/pt-BR"],
      // Mediana de 3 execuções: com 1 só, a variação de CPU do runner
      // compartilhado do GitHub decide o resultado (TBT oscila muito).
      numberOfRuns: 3,
    },
    assert: {
      assertions: {
        "categories:performance": ["error", { minScore: 0.9 }],
        "categories:accessibility": ["error", { minScore: 0.9 }],
        "categories:seo": ["error", { minScore: 0.9 }],
      },
    },
    upload: {
      target: "temporary-public-storage",
    },
  },
};
