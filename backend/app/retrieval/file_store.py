"""T043: `FileVectorStore` — busca por similaridade de cosseno com NumPy
sobre embeddings pré-calculados (decisão D4 de research.md: MVP sem banco
vetorial). Os arquivos são gerados por scripts/ingest.py.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np

from app.core.config import Settings
from app.retrieval.base import ScoredChunk
from app.retrieval.models import KnowledgeChunk, Lang

KB_DIR = Path(__file__).resolve().parents[2] / "data" / "kb"
CHUNKS_PATH = KB_DIR / "chunks.json"
VECTORS_PATH = KB_DIR / "vectors.npz"
MANIFEST_PATH = KB_DIR / "manifest.json"


class KnowledgeBaseNotReady(Exception):
    """A base de conhecimento não foi gerada ainda — rode scripts/ingest.py."""


class EmbeddingModelMismatch(Exception):
    """O manifest.json não corresponde ao modelo de embedding configurado."""


@lru_cache
def _load() -> tuple[list[KnowledgeChunk], np.ndarray, dict]:
    if not (CHUNKS_PATH.exists() and VECTORS_PATH.exists() and MANIFEST_PATH.exists()):
        raise KnowledgeBaseNotReady(
            f"Base de conhecimento ausente em {KB_DIR}. Rode `uv run python scripts/ingest.py`."
        )

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    chunks_raw = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    chunks = [KnowledgeChunk.model_validate(item) for item in chunks_raw]
    vectors = np.load(VECTORS_PATH)["vectors"]

    if len(chunks) != vectors.shape[0]:
        raise EmbeddingModelMismatch(
            f"chunks.json tem {len(chunks)} itens, mas vectors.npz tem {vectors.shape[0]}"
        )

    return chunks, vectors, manifest


def get_kb_manifest_hash() -> str:
    _, _, manifest = _load()
    return str(manifest.get("content_hash", "unknown"))


def assert_embedding_model_matches(settings: Settings) -> None:
    _, _, manifest = _load()
    configured = settings.gemini_embedding_model
    manifest_model = manifest.get("embedding_model")
    if manifest_model != configured:
        raise EmbeddingModelMismatch(
            f"manifest.json foi gerado com '{manifest_model}', mas o backend está "
            f"configurado para '{configured}'. Rode a ingestão de novo."
        )


class FileVectorStore:
    def __init__(self, settings: Settings) -> None:
        # Fail-fast: se o índice não corresponder ao modelo configurado, é
        # melhor falhar já na inicialização do que devolver buscas erradas.
        assert_embedding_model_matches(settings)

    def search(self, query_embedding: list[float], lang: Lang, top_k: int) -> list[ScoredChunk]:
        chunks, vectors, _ = _load()
        query = np.asarray(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query)
        if query_norm == 0:
            return []

        lang_mask = np.array([chunk.lang == lang for chunk in chunks])
        if not lang_mask.any():
            return []

        candidate_vectors = vectors[lang_mask]
        candidate_chunks = [c for c, keep in zip(chunks, lang_mask, strict=True) if keep]

        norms = np.linalg.norm(candidate_vectors, axis=1)
        norms[norms == 0] = 1e-9
        similarities = (candidate_vectors @ query) / (norms * query_norm)

        order = np.argsort(-similarities)[:top_k]
        return [ScoredChunk(chunk=candidate_chunks[i], score=float(similarities[i])) for i in order]
