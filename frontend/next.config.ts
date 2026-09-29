import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

// O backend Python roda como um projeto Vercel separado. Este rewrite faz o
// frontend chamar /api/* no mesmo domínio, evitando problemas de CORS.
// Em desenvolvimento local, aponta para o FastAPI local (uvicorn/fastapi dev).
const backendOrigin =
  process.env.BACKEND_ORIGIN ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendOrigin}/:path*`,
      },
    ];
  },
};

const withNextIntl = createNextIntlPlugin("./i18n/request.ts");

export default withNextIntl(nextConfig);
