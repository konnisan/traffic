from dataclasses import dataclass, field
from typing import Annotated

from langchain.agents import create_agent

from src.agents.common import BaseAgent, BaseContext, load_chat_model
from src.agents.common.middlewares import RuntimeConfigMiddleware
from src.agents.common.middlewares.knowledge_base_middleware import KnowledgeBaseMiddleware

from .tools import TRAFFIC_AUDIT_TOOLS

SYSTEM_PROMPT = """你是交通稽核辅助研判智能体。
回答案件问题时必须先调用交通稽核工具获取事实，不得自行推测通行记录、异常类型或收费金额。
每项异常都要说明源记录和规则依据。政策制度与历史案例只能通过已启用的知识库检索。
你只能提供辅助研判和报告解释，不得宣称案件已经正式定案，不得代替人工复核。
如果案件数据不完整或工具没有返回依据，明确说明无法判断。"""


@dataclass(kw_only=True)
class TrafficAuditContext(BaseContext):
    system_prompt: Annotated[str, {"__template_metadata__": {"kind": "prompt"}}] = field(
        default=SYSTEM_PROMPT,
        metadata={"name": "系统提示词", "description": "约束交通稽核智能体的事实来源和辅助研判边界"},
    )


class TrafficAuditAgent(BaseAgent):
    name = "交通稽核智能体"
    description = "基于确定性路径还原、异常证据和交通稽核知识库提供辅助研判。"
    context_schema = TrafficAuditContext

    async def get_graph(self, **kwargs):
        context = self.context_schema.from_file(module_name=self.module_name)
        return create_agent(
            model=load_chat_model(context.model),
            system_prompt=context.system_prompt,
            tools=TRAFFIC_AUDIT_TOOLS,
            middleware=[KnowledgeBaseMiddleware(), RuntimeConfigMiddleware(enable_tools_override=False)],
            checkpointer=await self._get_checkpointer(),
        )
