from __future__ import annotations

import os
import uuid
from typing import Any

import httpx

from src.repositories.dify_workflow_repository import DifyWorkflowRepository
from src.repositories.traffic_audit_repository import TrafficAuditRepository
from src.storage.postgres.manager import pg_manager
from src.storage.postgres.models_business import DifyWorkflowRun, TrafficAuditCase
from src.utils.datetime_utils import utc_now_naive

ALLOWED_WORKFLOWS = {
    "audit_report_draft": "DIFY_WORKFLOW_AUDIT_REPORT_DRAFT_ID",
    "policy_basis_summary": "DIFY_WORKFLOW_POLICY_BASIS_SUMMARY_ID",
    "green_vehicle_review_draft": "DIFY_WORKFLOW_GREEN_VEHICLE_REVIEW_DRAFT_ID",
}


class DifyWorkflowError(ValueError):
    pass


def _workflow_config(workflow_code: str) -> tuple[str, str, str]:
    if workflow_code not in ALLOWED_WORKFLOWS:
        raise DifyWorkflowError(f"Unsupported Dify workflow: {workflow_code}")

    api_url = (os.getenv("DIFY_WORKFLOW_API_URL") or os.getenv("DIFY_API_URL") or "").strip().rstrip("/")
    api_key = (os.getenv("DIFY_WORKFLOW_API_KEY") or "").strip()
    workflow_id = (os.getenv(ALLOWED_WORKFLOWS[workflow_code]) or "").strip()
    missing = [
        name
        for name, value in {
            "DIFY_WORKFLOW_API_URL": api_url,
            "DIFY_WORKFLOW_API_KEY": api_key,
            ALLOWED_WORKFLOWS[workflow_code]: workflow_id,
        }.items()
        if not value
    ]
    if missing:
        raise DifyWorkflowError(f"Dify workflow config missing: {', '.join(missing)}")
    return api_url, api_key, workflow_id


def build_case_workflow_inputs(case: TrafficAuditCase) -> dict[str, Any]:
    if not case.analysis_result:
        raise DifyWorkflowError("Case analysis result is required before running Dify workflow")
    return {
        "case_id": case.id,
        "title": case.title,
        "plate_number": case.plate_number,
        "time_window": {
            "started_at": case.started_at.isoformat(),
            "ended_at": case.ended_at.isoformat(),
        },
        "analysis_result": case.analysis_result,
        "existing_report_markdown": case.report_markdown or "",
        "review_status": {
            "status": case.status,
            "review_decision": case.review_decision,
            "review_comment": case.review_comment,
        },
    }


def extract_report_markdown(response_payload: dict[str, Any]) -> str | None:
    data = response_payload.get("data") if isinstance(response_payload, dict) else None
    outputs = data.get("outputs") if isinstance(data, dict) else response_payload.get("outputs")
    if not isinstance(outputs, dict):
        return None
    value = outputs.get("report_markdown") or outputs.get("markdown") or outputs.get("report")
    return str(value).strip() if value else None


def merge_dify_report(existing_report: str | None, dify_report: str | None) -> str | None:
    if not dify_report:
        return existing_report
    existing = (existing_report or "").rstrip()
    section = "## Dify 工作流报告草稿\n\n" + dify_report.strip()
    if not existing:
        return section
    return existing + "\n\n---\n\n" + section


async def create_case_workflow_run(
    *, case: TrafficAuditCase, workflow_code: str, created_by: str, task_id: str | None = None
) -> DifyWorkflowRun:
    _, _, workflow_id = _workflow_config(workflow_code)
    inputs = build_case_workflow_inputs(case)
    return DifyWorkflowRun(
        id=uuid.uuid4().hex,
        case_id=case.id,
        department_id=case.department_id,
        workflow_code=workflow_code,
        workflow_id=workflow_id,
        task_id=task_id,
        status="queued",
        request_payload={"inputs": inputs, "response_mode": "blocking", "user": created_by},
        created_by=created_by,
    )


async def execute_case_workflow(run_id: str) -> dict[str, Any]:
    async with pg_manager.get_async_session_context() as db:
        run_repository = DifyWorkflowRepository(db)
        case_repository = TrafficAuditRepository(db)
        run = await run_repository.get(run_id)
        if not run:
            raise DifyWorkflowError("Dify workflow run not found")
        case = await case_repository.get(run.case_id)
        if not case:
            raise DifyWorkflowError("Traffic audit case not found")

        api_url, api_key, workflow_id = _workflow_config(run.workflow_code)
        run.workflow_id = workflow_id
        run.status = "running"
        run.started_at = utc_now_naive()
        await run_repository.save(run)
        await db.commit()

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{api_url}/workflows/{workflow_id}/run",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json=run.request_payload,
                )
                response.raise_for_status()
                response_payload = response.json()
            run.status = "success"
            run.response_payload = response_payload
            run.completed_at = utc_now_naive()
            report_markdown = extract_report_markdown(response_payload)
            case.report_markdown = merge_dify_report(case.report_markdown, report_markdown)
            await case_repository.save(case)
            await run_repository.save(run)
            return run.to_dict()
        except Exception as exc:
            run.status = "failed"
            run.error_message = str(exc)
            run.completed_at = utc_now_naive()
            await run_repository.save(run)
            raise
