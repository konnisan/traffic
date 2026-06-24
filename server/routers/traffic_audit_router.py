from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from server.utils.auth_middleware import get_admin_user, get_db, get_required_user
from server.utils.common_utils import log_operation
from src.repositories.traffic_audit_repository import TrafficAuditRepository
from src.repositories.dify_workflow_repository import DifyWorkflowRepository
from src.services.dify_workflow_service import (
    DifyWorkflowError,
    create_case_workflow_run,
    execute_case_workflow,
)
from src.services.task_service import tasker
from src.services.traffic_audit_service import (
    TrafficAuditValidationError,
    new_case,
    parse_dataset,
    run_case_analysis,
)
from src.storage.postgres.models_business import TrafficAuditCase, User
from src.utils.datetime_utils import utc_now_naive

audit = APIRouter(prefix="/audit/cases", tags=["traffic-audit"])


class CaseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    plate_number: str = Field(min_length=1, max_length=32)
    started_at: datetime
    ended_at: datetime


class CaseReview(BaseModel):
    decision: Literal["confirmed", "rejected"]
    comment: str = Field(default="", max_length=2000)


def _department_scope(user: User) -> int | None:
    return None if user.role == "superadmin" else user.department_id


async def _require_case(repository: TrafficAuditRepository, case_id: str, user: User) -> TrafficAuditCase:
    case = await repository.get(case_id, _department_scope(user))
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    return case


@audit.post("")
async def create_case(
    payload: CaseCreate,
    request: Request,
    current_user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.department_id:
        raise HTTPException(status_code=400, detail="当前用户未绑定部门")
    try:
        case = new_case(
            title=payload.title,
            plate_number=payload.plate_number,
            started_at=payload.started_at,
            ended_at=payload.ended_at,
            department_id=current_user.department_id,
            created_by=current_user.user_id,
        )
    except TrafficAuditValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await TrafficAuditRepository(db).create(case)
    await log_operation(db, current_user.id, "创建交通稽核案件", f"案件ID: {case.id}", request)
    return {"case": case.to_dict(include_datasets=True)}


@audit.get("")
async def list_cases(
    current_user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    cases = await TrafficAuditRepository(db).list(_department_scope(current_user))
    return {"cases": [case.to_dict() for case in cases]}


@audit.get("/{case_id}")
async def get_case(
    case_id: str,
    current_user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    case = await _require_case(TrafficAuditRepository(db), case_id, current_user)
    return {"case": case.to_dict(include_datasets=True)}


@audit.post("/{case_id}/datasets")
async def upload_dataset(
    case_id: str,
    request: Request,
    dataset_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    repository = TrafficAuditRepository(db)
    case = await _require_case(repository, case_id, current_user)
    try:
        parsed = parse_dataset(dataset_type, file.filename or "upload.csv", await file.read())
    except (TrafficAuditValidationError, UnicodeDecodeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    datasets = dict(case.datasets or {})
    datasets[dataset_type] = parsed
    case.datasets = datasets
    case.analysis_result = None
    case.report_markdown = None
    case.task_id = None
    case.review_decision = None
    case.review_comment = None
    case.reviewed_by = None
    case.reviewed_at = None
    case.status = "ready" if set(datasets) == {"vehicles", "transactions", "passages"} else "draft"
    await repository.save(case)
    await log_operation(
        db,
        current_user.id,
        "上传交通稽核数据",
        f"案件ID: {case.id}, 数据集: {dataset_type}, 文件: {file.filename}",
        request,
    )
    return {"case": case.to_dict(include_datasets=True)}


@audit.post("/{case_id}/analyze")
async def analyze_case(
    case_id: str,
    request: Request,
    current_user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    repository = TrafficAuditRepository(db)
    case = await _require_case(repository, case_id, current_user)
    if case.status not in {"ready", "analysis_failed", "pending_review", "confirmed", "rejected"}:
        raise HTTPException(status_code=409, detail="请先上传全部三类数据")

    case.status = "queued"
    await repository.save(case)
    await db.commit()

    async def execute(context):
        await context.set_progress(10, "校验案件数据")
        result = await run_case_analysis(case_id)
        await context.set_progress(90, "生成结构化证据和报告草稿")
        return result

    task = await tasker.enqueue(
        name=f"交通稽核分析-{case.plate_number}",
        task_type="traffic_audit",
        payload={"case_id": case.id, "department_id": case.department_id},
        coroutine=execute,
    )
    case.task_id = task.id
    await repository.save(case)
    await log_operation(db, current_user.id, "启动交通稽核分析", f"案件ID: {case.id}, 任务ID: {task.id}", request)
    return {"task": task.to_summary_dict(), "case": case.to_dict()}


@audit.get("/{case_id}/task")
async def get_case_task(
    case_id: str,
    current_user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    case = await _require_case(TrafficAuditRepository(db), case_id, current_user)
    task = await tasker.get_task(case.task_id) if case.task_id else None
    return {"task": task}


@audit.get("/{case_id}/workflows")
async def list_case_workflows(
    case_id: str,
    current_user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    case = await _require_case(TrafficAuditRepository(db), case_id, current_user)
    runs = await DifyWorkflowRepository(db).list_by_case(case.id, _department_scope(current_user))
    return {"runs": [run.to_dict() for run in runs]}


@audit.post("/{case_id}/workflows/{workflow_code}/run")
async def run_case_workflow(
    case_id: str,
    workflow_code: Literal["audit_report_draft", "policy_basis_summary", "green_vehicle_review_draft"],
    request: Request,
    current_user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    repository = TrafficAuditRepository(db)
    case = await _require_case(repository, case_id, current_user)
    if not case.analysis_result:
        raise HTTPException(status_code=409, detail="case analysis result is required")

    try:
        run = await create_case_workflow_run(case=case, workflow_code=workflow_code, created_by=current_user.user_id)
    except DifyWorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await DifyWorkflowRepository(db).create(run)
    await db.commit()

    async def execute(context):
        await context.set_progress(10, "prepare Dify workflow input")
        if hasattr(context, "raise_if_cancelled"):
            await context.raise_if_cancelled()
        await context.set_progress(40, "璋冪敤 Dify Workflow")
        result = await execute_case_workflow(run.id)
        await context.set_progress(90, "save Dify workflow draft")
        return result

    task = await tasker.enqueue(
        name=f"Dify Workflow-{workflow_code}-{case.plate_number}",
        task_type="traffic_audit_dify_workflow",
        payload={"case_id": case.id, "workflow_run_id": run.id, "workflow_code": workflow_code},
        coroutine=execute,
    )
    run.task_id = task.id
    case.task_id = task.id
    await DifyWorkflowRepository(db).save(run)
    await repository.save(case)
    await log_operation(
        db,
        current_user.id,
        "Run Dify audit workflow",
        f"妗堜欢ID: {case.id}, Workflow: {workflow_code}, RunID: {run.id}, 浠诲姟ID: {task.id}",
        request,
    )
    return {"task": task.to_summary_dict(), "run": run.to_dict(), "case": case.to_dict()}


@audit.post("/{case_id}/review")
async def review_case(
    case_id: str,
    payload: CaseReview,
    request: Request,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    repository = TrafficAuditRepository(db)
    case = await _require_case(repository, case_id, current_user)
    if case.status != "pending_review":
        raise HTTPException(status_code=409, detail="只有待复核案件可以提交结论")
    case.review_decision = payload.decision
    case.review_comment = payload.comment.strip()
    case.reviewed_by = current_user.user_id
    case.reviewed_at = utc_now_naive()
    case.status = payload.decision
    conclusion = "人工确认异常" if payload.decision == "confirmed" else "人工驳回智能体结论"
    case.report_markdown = (case.report_markdown or "").replace("- 正式结论：未经人工确认", f"- 正式结论：{conclusion}")
    case.report_markdown += (
        "\n\n## 复核结论\n"
        f"- 结论：{conclusion}\n"
        f"- 复核人：{current_user.user_id}\n"
        f"- 意见：{payload.comment.strip() or '无'}\n"
    )
    await repository.save(case)
    await log_operation(
        db,
        current_user.id,
        "复核交通稽核案件",
        f"案件ID: {case.id}, 结论: {payload.decision}",
        request,
    )
    return {"case": case.to_dict()}


@audit.get("/{case_id}/report", response_class=PlainTextResponse)
async def download_report(
    case_id: str,
    current_user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    case = await _require_case(TrafficAuditRepository(db), case_id, current_user)
    if not case.report_markdown:
        raise HTTPException(status_code=404, detail="报告尚未生成")
    filename = f"traffic-audit-{case.id}.md"
    return PlainTextResponse(
        case.report_markdown,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
