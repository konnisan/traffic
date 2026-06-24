from __future__ import annotations

import json

from langgraph.prebuilt.tool_node import ToolRuntime
from pydantic import BaseModel, Field
from sqlalchemy import select

from src.agents.common.toolkits.registry import tool
from src.repositories.traffic_audit_repository import TrafficAuditRepository
from src.services.traffic_audit_service import analyze_case_data
from src.storage.postgres.manager import pg_manager
from src.storage.postgres.models_business import User


class CaseInput(BaseModel):
    case_id: str = Field(description="交通稽核案件ID")


async def _load_case(case_id: str, runtime: ToolRuntime):
    context = runtime.context
    department_id = getattr(context, "department_id", None)
    if not department_id:
        raise ValueError("当前用户未绑定部门")
    async with pg_manager.get_async_session_context() as db:
        user_id = getattr(context, "user_id", None)
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        scope = None if user and user.role == "superadmin" else department_id
        case = await TrafficAuditRepository(db).get(case_id, scope)
        if not case:
            raise ValueError("案件不存在或无权访问")
        return case


@tool(category="traffic_audit", tags=["稽核", "案件"], display_name="读取稽核案件", args_schema=CaseInput)
async def load_audit_case(case_id: str, runtime: ToolRuntime) -> str:
    """读取当前部门的交通稽核案件、数据摘要和人工复核状态。"""
    case = await _load_case(case_id, runtime)
    return json.dumps(case.to_dict(), ensure_ascii=False)


@tool(category="traffic_audit", tags=["稽核", "路径"], display_name="还原通行路径", args_schema=CaseInput)
async def reconstruct_audit_route(case_id: str, runtime: ToolRuntime) -> str:
    """使用确定性规则按事件时间还原案件车辆的通行路径。"""
    case = await _load_case(case_id, runtime)
    result = analyze_case_data(case)
    return json.dumps(result["route"], ensure_ascii=False)


@tool(category="traffic_audit", tags=["稽核", "证据"], display_name="查询异常证据", args_schema=CaseInput)
async def query_audit_evidence(case_id: str, runtime: ToolRuntime) -> str:
    """返回确定性规则识别的异常证据、源记录引用和规则依据。"""
    case = await _load_case(case_id, runtime)
    result = case.analysis_result or analyze_case_data(case)
    return json.dumps(result["evidence"], ensure_ascii=False)


@tool(category="traffic_audit", tags=["稽核", "报告"], display_name="读取稽核报告", args_schema=CaseInput)
async def load_audit_report(case_id: str, runtime: ToolRuntime) -> str:
    """读取已生成的稽核报告草稿；该工具不会生成或确认正式结论。"""
    case = await _load_case(case_id, runtime)
    return case.report_markdown or "案件尚未生成报告草稿"


TRAFFIC_AUDIT_TOOLS = [load_audit_case, reconstruct_audit_route, query_audit_evidence, load_audit_report]
