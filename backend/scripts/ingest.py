"""T041: gera a base de conhecimento do chat a partir de `frontend/content/`.

Uso:
    uv run python scripts/ingest.py

Lê os JSON/Markdown de cada idioma, quebra em trechos de ~150-300 tokens
(aproximados por número de palavras, para não depender de um tokenizer
específico neste script simples) e grava em backend/data/kb/:
    - chunks.json   (metadados + texto de cada KnowledgeChunk)
    - vectors.npz   (matriz de embeddings, mesma ordem de chunks.json)
    - manifest.json (modelo de embedding, dimensão, data, hash do conteúdo)

Reexecutar sempre que o conteúdo do autor mudar (ver .github/workflows/ingest.yml).
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

BACKEND_DIR = Path(__file__).resolve().parents[1]
FRONTEND_CONTENT_DIR = BACKEND_DIR.parent / "frontend" / "content"
KB_DIR = BACKEND_DIR / "data" / "kb"

sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings  # noqa: E402
from app.llm.gemini import GeminiLLMClient  # noqa: E402

LANGS = ["pt-BR", "en"]
# ~150-300 tokens ~= 110-220 palavras em português/inglês; usamos um alvo de
# palavras por trecho, simples e suficiente para este volume de conteúdo.
WORDS_PER_CHUNK = 180


def _chunk_text(text: str) -> list[str]:
    words = text.split()
    if not words:
        return []
    return [" ".join(words[i : i + WORDS_PER_CHUNK]) for i in range(0, len(words), WORDS_PER_CHUNK)]


def _profile_text(profile: dict) -> str:
    return f"{profile['name']} — {profile['headline']}. {profile['tagline']} {profile['summary']}"


def _experience_text(item: dict) -> str:
    end = item["end"] or "presente/present"
    return (
        f"{item['role']} em/at {item['organization']} ({item['start']} - {end}). "
        f"{item['description']} " + " ".join(item.get("highlights", []))
    )


def _project_text(item: dict) -> str:
    techs = ", ".join(item.get("technologies", []))
    return (
        f"Projeto/Project: {item['name']}. {item['description']} Tecnologias/Technologies: {techs}."
    )


def _certification_text(item: dict) -> str:
    return f"Certificação/Certification: {item['name']} — {item['issuer']} ({item['date']})."


def collect_source_records(lang: str) -> list[tuple[str, str, str]]:
    """Retorna tuplas (source, source_id, text) para um idioma."""
    lang_dir = FRONTEND_CONTENT_DIR / lang
    records: list[tuple[str, str, str]] = []

    profile = json.loads((lang_dir / "profile.json").read_text(encoding="utf-8"))
    records.append(("profile", "profile", _profile_text(profile)))

    timeline = json.loads((lang_dir / "timeline.json").read_text(encoding="utf-8"))
    for item in timeline["items"]:
        records.append(("experience", item["id"], _experience_text(item)))

    projects = json.loads((lang_dir / "projects.json").read_text(encoding="utf-8"))
    for item in projects["items"]:
        records.append(("project", item["id"], _project_text(item)))

    certifications = json.loads((lang_dir / "certifications.json").read_text(encoding="utf-8"))
    for item in certifications["items"]:
        records.append(("certification", item["id"], _certification_text(item)))

    cv_path = lang_dir / "cv.md"
    if cv_path.exists():
        records.append(("cv", "cv", cv_path.read_text(encoding="utf-8")))

    return records


def compute_content_hash() -> str:
    hasher = hashlib.sha256()
    for path in sorted(FRONTEND_CONTENT_DIR.rglob("*")):
        if path.is_file():
            hasher.update(path.read_bytes())
    return hasher.hexdigest()


def main() -> None:
    settings = get_settings()
    llm = GeminiLLMClient(settings)

    chunk_records: list[dict] = []
    chunk_texts: list[str] = []

    for lang in LANGS:
        for source, source_id, text in collect_source_records(lang):
            for i, chunk_text in enumerate(_chunk_text(text)):
                chunk_records.append(
                    {
                        "id": f"{lang}:{source}:{source_id}:{i}",
                        "lang": lang,
                        "source": source,
                        "source_id": source_id,
                        "text": chunk_text,
                    }
                )
                chunk_texts.append(chunk_text)

    if not chunk_texts:
        raise SystemExit("Nenhum trecho de conteúdo encontrado — verifique frontend/content/.")

    print(f"Gerando embeddings para {len(chunk_texts)} trechos...")
    embeddings = llm.embed(chunk_texts)
    vectors = np.array(embeddings, dtype=np.float32)

    KB_DIR.mkdir(parents=True, exist_ok=True)
    (KB_DIR / "chunks.json").write_text(
        json.dumps(chunk_records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    np.savez_compressed(KB_DIR / "vectors.npz", vectors=vectors)

    manifest = {
        "embedding_model": settings.gemini_embedding_model,
        "dimension": vectors.shape[1] if vectors.ndim == 2 else 0,
        "chunk_count": len(chunk_records),
        "generated_at": datetime.now(UTC).isoformat(),
        "content_hash": compute_content_hash(),
    }
    (KB_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"OK: {len(chunk_records)} trechos gravados em {KB_DIR}")


if __name__ == "__main__":
    main()
