from src.agents.traffic_audit.graph import SYSTEM_PROMPT
from src.agents.traffic_audit.tools import TRAFFIC_AUDIT_TOOLS


def test_traffic_audit_agent_exposes_only_read_only_case_tools():
    names = {tool.name for tool in TRAFFIC_AUDIT_TOOLS}

    assert names == {
        "load_audit_case",
        "reconstruct_audit_route",
        "query_audit_evidence",
        "load_audit_report",
    }
    assert "不得宣称案件已经正式定案" in SYSTEM_PROMPT
