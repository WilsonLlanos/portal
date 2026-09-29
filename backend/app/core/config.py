"""T014: configuração central do backend (Pydantic Settings).

Lê as variáveis de `.env` (ver `.env.example`). Nenhum valor default aqui
contém segredo real — apenas defaults operacionais (limites, nomes de
modelo) que fazem sentido documentar no código.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM (decisão O1 do plan.md: camada paga do Gemini)
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-3.1-flash-lite")
    gemini_embedding_model: str = Field(default="gemini-embedding-001")

    # Guardrail (decisão O2 do plan.md: Groq com cartão cadastrado)
    groq_api_key: str = Field(default="")
    groq_guard_model: str = Field(default="meta-llama/llama-prompt-guard-2-86m")
    guard_timeout_seconds: float = Field(default=2.0)

    # Estado compartilhado (Upstash Redis)
    upstash_redis_rest_url: str = Field(default="")
    upstash_redis_rest_token: str = Field(default="")

    # Observabilidade (Langfuse)
    langfuse_public_key: str = Field(default="")
    langfuse_secret_key: str = Field(default="")
    langfuse_host: str = Field(default="https://cloud.langfuse.com")

    # Limites do chat (decisão O3 do plan.md)
    max_message_length: int = Field(default=500)
    daily_cost_cap_cents: int = Field(default=50)
    rate_limit_per_hour: int = Field(default=20)

    # CORS (dev local; em produção o frontend chama via rewrite no mesmo domínio)
    cors_allow_origins: str = Field(default="http://127.0.0.1:3000,http://localhost:3000")

    @property
    def cors_allow_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
