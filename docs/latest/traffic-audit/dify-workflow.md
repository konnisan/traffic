# Dify 工作流接入规范

Dify 在一期中是外部编排器，不是案件事实系统。后端只允许调用白名单工作流，前端不得传入任意 Dify URL、API Key 或 workflow id。

具体可在 Dify 页面中创建的节点模板见 [Dify 工作流模板](./dify-workflows.md)。

## 固定工作流

- `audit_report_draft`：根据结构化案件结果生成报告草稿。
- `policy_basis_summary`：根据异常类型和规则依据生成政策摘要。
- `green_vehicle_review_draft`：根据绿通申报信息生成辅助核查草稿。

## 输入

后端传入 Dify 的 `inputs` 来自案件结构化结果：

```json
{
  "case_id": "...",
  "title": "...",
  "plate_number": "...",
  "time_window": {
    "started_at": "...",
    "ended_at": "..."
  },
  "analysis_result": {
    "route": [],
    "evidence": [],
    "risk_summary": "..."
  },
  "existing_report_markdown": "...",
  "review_status": {
    "status": "pending_review",
    "review_decision": null,
    "review_comment": null
  }
}
```

## 输出

推荐 Dify 输出：

```json
{
  "report_markdown": "...",
  "basis_summary": "...",
  "missing_evidence_questions": []
}
```

如果返回 `report_markdown`，后端会追加到现有报告的 “Dify 工作流报告草稿” 区域。Dify 输出始终是草稿，不改变人工复核状态。

## 调用留痕

每次调用写入 `dify_workflow_runs`，保存 workflow code、workflow id、输入快照、输出、错误、Tasker 任务 ID 和创建人。

## 和轻量 Workflow Core 的关系

Dify 是一个可选组件，不是主流程本身。轻量 Workflow Core 负责节点选择、连线、运行记录和权限控制；当用户选择 `dify.workflow.audit_report_draft` 这类节点时，后端再调用 Dify。

也就是说：

- 案件事实：由 FastAPI 确定性组件产生。
- 节点编排：由轻量 Workflow Core 保存和执行。
- 文本生成：由 Dify Workflow 或本地 LLM 组件完成。
- 正式结论：由人工复核产生。
