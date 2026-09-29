"""T035: VectorStore ordena por similaridade decrescente e respeita o
filtro de idioma (contrato em contracts/provider-interfaces.md).
"""

import json

import numpy as np
import pytest

from app.core.config import Settings
from app.retrieval import file_store


def _write_kb(tmp_path, embedding_model="test-model"):
    chunks = [
        {
            "id": "pt:profile:profile:0",
            "lang": "pt-BR",
            "source": "profile",
            "source_id": "profile",
            "text": "pt A",
        },
        {
            "id": "pt:profile:profile:1",
            "lang": "pt-BR",
            "source": "profile",
            "source_id": "profile",
            "text": "pt B",
        },
        {
            "id": "en:profile:profile:0",
            "lang": "en",
            "source": "profile",
            "source_id": "profile",
            "text": "en A",
        },
    ]
    # Vetores 2D simples e conhecidos, para prever a ordem de similaridade.
    vectors = np.array(
        [
            [1.0, 0.0],  # pt A
            [0.0, 1.0],  # pt B
            [1.0, 0.0],  # en A
        ],
        dtype=np.float32,
    )
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "chunks.json").write_text(json.dumps(chunks), encoding="utf-8")
    np.savez_compressed(kb_dir / "vectors.npz", vectors=vectors)
    manifest = {"embedding_model": embedding_model, "content_hash": "abc123"}
    (kb_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return kb_dir


@pytest.fixture(autouse=True)
def _reset_cache():
    file_store._load.cache_clear()
    yield
    file_store._load.cache_clear()


def _patch_paths(monkeypatch, kb_dir):
    monkeypatch.setattr(file_store, "KB_DIR", kb_dir)
    monkeypatch.setattr(file_store, "CHUNKS_PATH", kb_dir / "chunks.json")
    monkeypatch.setattr(file_store, "VECTORS_PATH", kb_dir / "vectors.npz")
    monkeypatch.setattr(file_store, "MANIFEST_PATH", kb_dir / "manifest.json")


def _settings(embedding_model="test-model") -> Settings:
    return Settings(gemini_embedding_model=embedding_model)


def test_search_orders_by_similarity_desc(tmp_path, monkeypatch):
    kb_dir = _write_kb(tmp_path)
    _patch_paths(monkeypatch, kb_dir)

    store = file_store.FileVectorStore(_settings())
    # Query próxima de "pt A" ([1,0]) — deve vir primeiro.
    results = store.search([0.9, 0.1], lang="pt-BR", top_k=2)

    assert [r.chunk.id for r in results] == ["pt:profile:profile:0", "pt:profile:profile:1"]
    assert results[0].score > results[1].score


def test_search_filters_by_lang(tmp_path, monkeypatch):
    kb_dir = _write_kb(tmp_path)
    _patch_paths(monkeypatch, kb_dir)

    store = file_store.FileVectorStore(_settings())
    results = store.search([1.0, 0.0], lang="en", top_k=5)

    assert len(results) == 1
    assert results[0].chunk.lang == "en"


def test_embedding_model_mismatch_raises(tmp_path, monkeypatch):
    kb_dir = _write_kb(tmp_path, embedding_model="other-model")
    _patch_paths(monkeypatch, kb_dir)

    with pytest.raises(file_store.EmbeddingModelMismatch):
        file_store.FileVectorStore(_settings(embedding_model="test-model"))
