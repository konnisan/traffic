from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any

from src import config


class VisualRagService:
    """Small local visual RAG PoC index.

    The current implementation stores rendered PDF pages and page text metadata.
    A ColPali/ColQwen provider can replace _score_page without changing the API.
    """

    def __init__(self, root_dir: str | None = None):
        self.root_dir = Path(root_dir or os.path.join(config.save_dir, "visual_rag"))
        self.root_dir.mkdir(parents=True, exist_ok=True)

    async def index_document(self, filename: str, content: bytes) -> dict[str, Any]:
        suffix = Path(filename).suffix.lower()
        if suffix != ".pdf":
            raise ValueError("visual_rag PoC currently supports PDF files only")

        import fitz

        index_id = f"vr_{uuid.uuid4().hex[:16]}"
        work_dir = self.root_dir / index_id
        page_dir = work_dir / "pages"
        page_dir.mkdir(parents=True, exist_ok=True)

        source_path = work_dir / filename
        source_path.write_bytes(content)

        pages = []
        with fitz.open(stream=content, filetype="pdf") as doc:
            for page_index, page in enumerate(doc, start=1):
                pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                image_path = page_dir / f"page_{page_index}.png"
                pixmap.save(image_path)
                text = page.get_text("text") or ""
                image_bytes = image_path.read_bytes()
                pages.append(
                    {
                        "doc_id": index_id,
                        "filename": filename,
                        "page_no": page_index,
                        "image_path": str(image_path),
                        "page_hash": hashlib.sha256(image_bytes).hexdigest(),
                        "text": text,
                        "embedding_provider": "colpali_compatible_poc",
                    }
                )

        index = {
            "index_id": index_id,
            "filename": filename,
            "page_count": len(pages),
            "embedding_provider": "colpali_compatible_poc",
            "pages": pages,
        }
        (work_dir / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
        return {k: v for k, v in index.items() if k != "pages"} | {"pages": self._public_pages(pages)}

    async def query(self, index_id: str, query: str, top_k: int = 5) -> dict[str, Any]:
        index = self._load_index(index_id)
        scored = []
        for page in index["pages"]:
            score = self._score_page(query, page.get("text") or "")
            scored.append(page | {"score": score})
        scored.sort(key=lambda item: item["score"], reverse=True)
        return {
            "index_id": index_id,
            "query": query,
            "provider": index.get("embedding_provider"),
            "results": self._public_pages(scored[: max(1, top_k)]),
        }

    def _load_index(self, index_id: str) -> dict[str, Any]:
        if not re.fullmatch(r"vr_[a-f0-9]{16}", index_id or ""):
            raise ValueError("Invalid visual_rag index_id")
        index_path = self.root_dir / index_id / "index.json"
        if not index_path.exists():
            raise ValueError(f"visual_rag index not found: {index_id}")
        return json.loads(index_path.read_text(encoding="utf-8"))

    @staticmethod
    def _score_page(query: str, text: str) -> float:
        query_terms = {term.lower() for term in re.findall(r"[\w\u4e00-\u9fff]+", query or "") if term.strip()}
        if not query_terms:
            return 0.0
        text_lower = (text or "").lower()
        hits = sum(1 for term in query_terms if term in text_lower)
        return hits / len(query_terms)

    @staticmethod
    def _public_pages(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "doc_id": page.get("doc_id"),
                "filename": page.get("filename"),
                "page_no": page.get("page_no"),
                "image_path": page.get("image_path"),
                "page_hash": page.get("page_hash"),
                "score": page.get("score"),
                "text_preview": (page.get("text") or "")[:500],
                "embedding_provider": page.get("embedding_provider"),
            }
            for page in pages
        ]
