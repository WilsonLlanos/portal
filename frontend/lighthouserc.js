/** T066: Lighthouse CI — meta de SC-004 (>90 em desempenho, acessibilidade, SEO). */
module.exports = {
  ci: {
    collect: {
      startServerCommand: "npm run start",
      url: ["http://127.0.0.1:3000/pt-BR"],
      numberOfRuns: 1,
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
