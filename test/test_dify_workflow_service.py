from datetime import datetime

import pytest

from src.services.dify_workflow_service import (
    DifyWorkflowError,
    _workflow_config,
    build_case_workflow_inputs,
    extract_report_markdown,
    merge_dify_report,
)
from src.services.traffic_audit_service import new_case


def test_workflow_config_requires_whitelisted_code(monkeypatch):
    monkeypatch.setenv("DIFY_WORKFLOW_API_URL", "https://dify.example/v1")
    monkeypatch.setenv("DIFY_WORKFLOW_API_KEY", "token")
    monkeypatch.setenv("DIFY_WORKFLOW_AUDIT_REPORT_DRAFT_ID", "workflow-1")

    assert _workflow_config("audit_report_draft") == ("https://dify.example/v1", "token", "workflow-1")
    with pytest.raises(DifyWorkflowError, match="Unsupported"):
        _workflow_config("free_text_workflow")


def test_case_workflow_inputs_require_deterministic_analysis():
    case = new_case(
        title="audit case",
        plate_number="ABC123",
        started_at=datetime(2026, 1, 1, 8),
        ended_at=datetime(2026, 1, 1, 9),
        department_id=1,
        created_by="pytest",
    )

    with pytest.raises(DifyWorkflowError, match="analysis result"):
        build_case_workflow_inputs(case)

    case.analysis_result = {"route": [], "evidence": [], "risk_summary": "ok"}
    case.report_markdown = "# deterministic draft"
    inputs = build_case_workflow_inputs(case)

    assert inputs["case_id"] == case.id
    assert inputs["analysis_result"] == case.analysis_result
    assert inputs["existing_report_markdown"] == "# deterministic draft"


def test_extract_and_merge_dify_report_keeps_draft_boundary():
    payload = {"data": {"outputs": {"report_markdown": "# Dify draft"}}}

    merged = merge_dify_report("- 正式结论：未经人工确认", extract_report_markdown(payload))

    assert "## Dify 工作流报告草稿" in merged
    assert "# Dify draft" in merged
    assert "- 正式结论：未经人工确认" in merged
