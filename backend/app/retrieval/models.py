"""T018: modelo `KnowledgeChunk`, conforme
specs/001-portfolio-portal/data-model.md § 2. Gerado pelo script de ingestão
(scripts/ingest.py) — não é editado à mão.
"""

from typing import Literal

from pydantic import BaseModel

Lang = Literal["pt-BR", "en"]
Source = Literal["profile", "experience", "project", "certification", "cv"]


class KnowledgeChunk(BaseModel):
    id: str
    lang: Lang
    source: Source
    source_id: str
    text: str
