from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

import server.routers.traffic_audit_router as audit_router
from server.utils.auth_middleware import get_db, get_required_user
from src.services.task_service import Task


class FakeDB:
    async def commit(self):
        return None


class FakeRepository:
    cases = {}

    def __init__(self, db):
        self.db = db

    async def create(self, case):
        self.cases[case.id] = case
        return case

    async def get(self, case_id, department_id=None):
        case = self.cases.get(case_id)
        if case and department_id is not None and case.department_id != department_id:
            return None
        return case

    async def list(self, department_id=None):
        return [
            case for case in self.cases.values() if department_id is None or case.department_id == department_id
        ]

    async def save(self, case):
        self.cases[case.id] = case
        return case


class FakeTasker:
    def __init__(self):
        self.task = None

    async def enqueue(self, *, name, task_type, payload, coroutine):
        self.task = Task(id="task-1", name=name, type=task_type, payload=payload)
        context = SimpleNamespace(
            set_progress=self._set_progress,
        )
        await coroutine(context)
        self.task.status = "success"
        return self.task

    async def _set_progress(self, progress, message):
        self.task.progress = progress
        self.task.message = message

    async def get_task(self, task_id):
        return self.task.to_dict() if self.task and self.task.id == task_id else None


class FakeWorkflowRun:
    def __init__(self, case, workflow_code, created_by):
        self.id = "workflow-run-1"
        self.case_id = case.id
        self.department_id = case.department_id
        self.workflow_code = workflow_code
        self.workflow_id = "workflow-1"
        self.task_id = None
        self.status = "queued"
        self.created_by = created_by

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "department_id": self.department_id,
            "workflow_code": self.workflow_code,
            "workflow_id": self.workflow_id,
            "task_id": self.task_id,
            "status": self.status,
            "created_by": self.created_by,
        }


class FakeWorkflowRepository:
    runs = {}

    def __init__(self, db):
        self.db = db

    async def create(self, run):
        self.runs[run.id] = run
        return run

    async def list_by_case(self, case_id, department_id=None):
        return [
            run
            for run in self.runs.values()
            if run.case_id == case_id and (department_id is None or run.department_id == department_id)
        ]

    async def save(self, run):
        self.runs[run.id] = run
        return run


def build_client(monkeypatch, user):
    app = FastAPI()
    app.include_router(audit_router.audit, prefix="/api")
    fake_tasker = FakeTasker()

    async def current_user():
        return user

    async def db():
        yield FakeDB()

    async def no_log(*args, **kwargs):
        return None

    async def analyze(case_id):
        case = FakeRepository.cases[case_id]
        case.status = "pending_review"
        case.analysis_result = {"route": [], "evidence": [], "risk_summary": "未发现规则异常"}
        case.report_markdown = "# 报告"
        return case.analysis_result

    async def create_workflow_run(*, case, workflow_code, created_by):
        return FakeWorkflowRun(case, workflow_code, created_by)

    async def execute_workflow(run_id):
        run = FakeWorkflowRepository.runs[run_id]
        run.status = "success"
        return run.to_dict()

    app.dependency_overrides[get_required_user] = current_user
    app.dependency_overrides[get_db] = db
    monkeypatch.setattr(audit_router, "TrafficAuditRepository", FakeRepository)
    monkeypatch.setattr(audit_router, "DifyWorkflowRepository", FakeWorkflowRepository)
    monkeypatch.setattr(audit_router, "tasker", fake_tasker)
    monkeypatch.setattr(audit_router, "log_operation", no_log)
    monkeypatch.setattr(audit_router, "run_case_analysis", analyze)
    monkeypatch.setattr(audit_router, "create_case_workflow_run", create_workflow_run)
    monkeypatch.setattr(audit_router, "execute_case_workflow", execute_workflow)
    return TestClient(app)


def test_case_lifecycle_requires_all_datasets_and_admin_review(monkeypatch):
    FakeRepository.cases = {}
    user = SimpleNamespace(id=1, user_id="auditor", role="user", department_id=10)
    client = build_client(monkeypatch, user)
    created = client.post(
        "/api/audit/cases",
        json={
            "title": "接口测试案件",
            "plate_number": "鄂A10001",
            "started_at": "2026-01-02T07:00:00",
            "ended_at": "2026-01-02T10:00:00",
        },
    )
    assert created.status_code == 200
    case_id = created.json()["case"]["id"]

    blocked = client.post(f"/api/audit/cases/{case_id}/analyze")
    assert blocked.status_code == 409

    fixture_dir = __import__("pathlib").Path(__file__).parents[1] / "fixtures" / "traffic_audit"
    for dataset_type in ("vehicles", "transactions", "passages"):
        path = fixture_dir / f"{dataset_type}.csv"
        uploaded = client.post(
            f"/api/audit/cases/{case_id}/datasets",
            data={"dataset_type": dataset_type},
            files={"file": (path.name, path.read_bytes(), "text/csv")},
        )
        assert uploaded.status_code == 200

    analyzed = client.post(f"/api/audit/cases/{case_id}/analyze")
    assert analyzed.status_code == 200
    assert client.get(f"/api/audit/cases/{case_id}/task").json()["task"]["status"] == "success"

    denied = client.post(
        f"/api/audit/cases/{case_id}/review",
        json={"decision": "confirmed", "comment": "复核通过"},
    )
    assert denied.status_code == 403

    user.role = "admin"
    reviewed = client.post(
        f"/api/audit/cases/{case_id}/review",
        json={"decision": "confirmed", "comment": "复核通过"},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["case"]["status"] == "confirmed"


def test_department_scope_hides_other_department_case(monkeypatch):
    FakeRepository.cases = {}
    owner = SimpleNamespace(id=1, user_id="owner", role="user", department_id=10)
    owner_client = build_client(monkeypatch, owner)
    created = owner_client.post(
        "/api/audit/cases",
        json={
            "title": "部门隔离案件",
            "plate_number": "鄂A10001",
            "started_at": datetime(2026, 1, 2, 7).isoformat(),
            "ended_at": datetime(2026, 1, 2, 10).isoformat(),
        },
    ).json()["case"]

    other = SimpleNamespace(id=2, user_id="other", role="user", department_id=20)
    other_client = build_client(monkeypatch, other)
    assert other_client.get(f"/api/audit/cases/{created['id']}").status_code == 404


def test_dify_workflow_runs_only_after_case_analysis(monkeypatch):
    FakeRepository.cases = {}
    FakeWorkflowRepository.runs = {}
    user = SimpleNamespace(id=1, user_id="auditor", role="user", department_id=10)
    client = build_client(monkeypatch, user)
    created = client.post(
        "/api/audit/cases",
        json={
            "title": "workflow case",
            "plate_number": "ABC123",
            "started_at": "2026-01-02T07:00:00",
            "ended_at": "2026-01-02T10:00:00",
        },
    ).json()["case"]

    blocked = client.post(f"/api/audit/cases/{created['id']}/workflows/audit_report_draft/run")
    assert blocked.status_code == 409

    case = FakeRepository.cases[created["id"]]
    case.analysis_result = {"route": [], "evidence": [], "risk_summary": "ok"}
    case.report_markdown = "# deterministic report"
    case.status = "pending_review"

    started = client.post(f"/api/audit/cases/{case.id}/workflows/audit_report_draft/run")
    assert started.status_code == 200
    payload = started.json()
    assert payload["run"]["workflow_code"] == "audit_report_draft"
    assert payload["task"]["type"] == "traffic_audit_dify_workflow"

    runs = client.get(f"/api/audit/cases/{case.id}/workflows").json()["runs"]
    assert runs[0]["status"] == "success"
