# Dify 工作流模板

这里给出一期需要在 Dify 中手工创建的三个工作流模板。它们不是案件事实系统，只接收后端生成的结构化 JSON，并输出报告草稿、政策摘要或辅助核查意见。

后端只保存 Dify 的 `workflow_id`，不让前端传入任意 Dify 地址或 API Key。

## 1. audit_report_draft

用途：根据交通稽核确定性分析结果生成报告草稿。

### 输入变量

| 变量名 | 类型 | 说明 |
| --- | --- | --- |
| `case_id` | string | 案件 ID |
| `title` | string | 案件标题 |
| `plate_number` | string | 车牌号 |
| `time_window` | object | 分析时间窗 |
| `analysis_result` | object | 后端结构化分析结果 |
| `existing_report_markdown` | string | 后端基础报告 |
| `review_status` | object | 当前复核状态 |

### 节点建议

```mermaid
flowchart LR
  Start["Start: 接收案件 JSON"] --> Check["Code: 校验证据和路径"]
  Check --> LLM["LLM: 生成稽核报告草稿"]
  LLM --> Format["Code: 输出 JSON"]
  Format --> End["End: report_markdown"]
```

### LLM 提示词

```text
你是交通稽核报告助手。你只能根据输入的 analysis_result、existing_report_markdown 和证据项生成报告草稿。

要求：
1. 不得新增输入中不存在的源记录、政策依据、金额、时间或车牌。
2. 每个异常结论必须引用 evidence 中的 evidence_id、rule_id 和 source_refs。
3. 结论只能写为“疑似异常”或“建议人工复核”，不得写成正式处罚结论。
4. 输出 Markdown。

输入：
{{ analysis_result }}

已有报告：
{{ existing_report_markdown }}
```

### 输出变量

```json
{
  "report_markdown": "## 案件概述\n...\n",
  "missing_evidence_questions": []
}
```

## 2. policy_basis_summary

用途：根据异常类型、规则编号和 Dify Dataset 检索结果生成依据摘要。

### 输入变量

| 变量名 | 类型 | 说明 |
| --- | --- | --- |
| `case_id` | string | 案件 ID |
| `evidence` | array | 证据项列表 |
| `rule_ids` | array | 后端命中的规则编号 |
| `retrieved_context` | string | Dify Dataset 或后端 RAG 返回的依据文本 |

### 节点建议

```mermaid
flowchart LR
  Start["Start"] --> Knowledge["Knowledge Retrieval: 政策/规则/案例库"]
  Knowledge --> LLM["LLM: 依据摘要"]
  LLM --> End["End: basis_summary"]
```

### LLM 提示词

```text
你是交通稽核政策依据整理助手。请根据检索到的制度、规则、案例文本，为 evidence 中的异常类型整理依据摘要。

要求：
1. 只引用 retrieved_context 中出现的内容。
2. 如果依据不足，明确写“未检索到充分依据”。
3. 输出应包含 rule_id、异常类型、依据摘要、引用片段。
4. 不得把政策摘要写成最终定案意见。

证据：
{{ evidence }}

检索上下文：
{{ retrieved_context }}
```

### 输出变量

```json
{
  "basis_summary": [
    {
      "rule_id": "missing_entry",
      "summary": "...",
      "quote": "..."
    }
  ]
}
```

## 3. green_vehicle_review_draft

用途：生成绿通辅助核查草稿。

### 输入变量

| 变量名 | 类型 | 说明 |
| --- | --- | --- |
| `case_id` | string | 案件 ID |
| `plate_number` | string | 车牌号 |
| `declared_goods` | string | 申报货物 |
| `passage_events` | array | 通行事件摘要 |
| `transaction_summary` | object | 交易摘要 |
| `attachments_summary` | string | 附件或人工录入摘要 |

### 节点建议

```mermaid
flowchart LR
  Start["Start"] --> LLM["LLM: 绿通核查问题清单"]
  LLM --> End["End: review_markdown"]
```

### LLM 提示词

```text
你是绿通辅助核查助手。请根据输入信息生成复核草稿。

要求：
1. 只能提出核查问题和风险点，不能判断为违规。
2. 不得编造货物照片、称重信息、车辆轨迹或收费记录。
3. 对缺失信息生成待补充清单。
4. 输出 Markdown。

输入：
{{ plate_number }}
{{ declared_goods }}
{{ passage_events }}
{{ transaction_summary }}
{{ attachments_summary }}
```

### 输出变量

```json
{
  "review_markdown": "## 绿通辅助核查\n...",
  "missing_fields": []
}
```

## 后端环境变量

```bash
DIFY_WORKFLOW_API_URL=https://your-dify.example.com/v1
DIFY_WORKFLOW_API_KEY=app-xxx
DIFY_WORKFLOW_AUDIT_REPORT_DRAFT_ID=xxx
DIFY_WORKFLOW_POLICY_BASIS_SUMMARY_ID=xxx
DIFY_WORKFLOW_GREEN_VEHICLE_REVIEW_DRAFT_ID=xxx
```

## 调用边界

- Dify 输出只保存为草稿。
- 后端稽核规则输出才是结构化事实。
- 人工复核后才能形成正式结论。
- Dify 失败不得影响案件事实结果。
