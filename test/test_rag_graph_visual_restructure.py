from __future__ import annotations

import os

os.environ.setdefault("YUXI_DISABLE_GRAPH_INIT", "1")

import pytest

from src.knowledge.chunking.ragflow_like.presets import get_default_chunk_parser_config
from src.services.graph_triple_service import GraphTripleService
from src.services.visual_rag_service import VisualRagService


class FakeTripleRepo:
    def __init__(self):
        self.rows = []

    async def create_many(self, items):
        self.rows = [FakeRow(item) for item in items]
        return self.rows

    async def list(self, status=None, source_kind=None, limit=100):
        rows = self.rows
        if status:
            rows = [row for row in rows if row.status == status]
        if source_kind:
            rows = [row for row in rows if row.source_kind == source_kind]
        return rows[:limit]

    async def get(self, triple_id):
        return next((row for row in self.rows if row.triple_id == triple_id), None)

    async def update_status(self, triple_id, status, reviewed_by, review_comment=None):
        row = await self.get(triple_id)
        if not row:
            return None
        row.status = status
        row.reviewed_by = reviewed_by
        row.review_comment = review_comment
        return row


class FakeRow:
    def __init__(self, data):
        self.__dict__.update(data)
        self.review_comment = data.get("review_comment")
        self.reviewed_by = data.get("reviewed_by")
        self.approved_at = None
        self.created_at = None
        self.updated_at = None


def test_general_chunk_preset_does_not_enable_graphrag_by_default():
    config = get_default_chunk_parser_config("general")

    assert config["graphrag"]["use_graphrag"] is False


@pytest.mark.asyncio
async def test_graph_triples_import_as_draft_and_convert_to_graph_payload():
    repo = FakeTripleRepo()
    service = GraphTripleService(repo)
    csv_data = (
        "subject,predicate,object,subject_type,object_type,source_doc_id,source_page,source_quote,confidence\n"
        "入口缺失,需要证据,入口事件记录,异常类型,证据项,rule-001,3,入口缺失应核查入口流水,0.95\n"
    ).encode()

    result = await service.import_file("triples.csv", csv_data, "admin")
    triple = result["triples"][0]

    assert result["imported"] == 1
    assert triple["status"] == "draft"
    assert triple["source_kind"] == "curated_triples"
    assert triple["source_page"] == 3

    reviewed = await service.review_triple(triple["triple_id"], "approve", "admin")
    payload = GraphTripleService.to_graph_payload(reviewed)

    assert reviewed["status"] == "approved"
    assert payload["h"]["name"] == "入口缺失"
    assert payload["r"]["type"] == "需要证据"
    assert payload["r"]["source_quote"] == "入口缺失应核查入口流水"
    assert payload["t"]["name"] == "入口事件记录"


@pytest.mark.asyncio
async def test_visual_rag_indexes_pdf_pages_and_returns_page_evidence(tmp_path):
    import fitz

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Traffic audit fee mismatch evidence")
    content = pdf.tobytes()
    pdf.close()

    service = VisualRagService(root_dir=str(tmp_path))
    indexed = await service.index_document("evidence.pdf", content)
    result = await service.query(indexed["index_id"], "fee mismatch", top_k=1)

    assert indexed["page_count"] == 1
    assert indexed["pages"][0]["page_no"] == 1
    assert result["results"][0]["page_no"] == 1
    assert result["results"][0]["score"] > 0
