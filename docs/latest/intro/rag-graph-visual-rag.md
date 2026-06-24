# RAG、知识图谱与视觉检索分层

Yuxi-Know 默认不应把任意文件都自动抽取为知识图谱。对于需要审计、稽核、合规追溯的场景，知识体系按来源和风险分层处理。

## 三类知识入口

| 类型 | 适用内容 | 实现方式 | 是否自动写正式图谱 |
| --- | --- | --- | --- |
| Text RAG | 政策、制度、规则、案例文本 | Markdown 解析、分片、向量检索 | 否 |
| Graph RAG | 专业三元组、已审核关系 | 草稿导入、人工审核、Neo4j 写入 | 仅审核通过后 |
| Visual RAG | 扫描 PDF、表格 PDF、版式强文档 | 页级图片索引，ColPali 兼容 PoC | 否 |

业务流水、交易记录、通行事件不进入 RAG 或知识图谱，应由确定性程序处理。

## 图谱治理

人工三元组导入支持 `jsonl`、`csv`、`xlsx`、`xlsm`。推荐字段：

```json
{"subject":"入口缺失","predicate":"需要证据","object":"入口事件记录","subject_type":"异常类型","object_type":"证据项","source_doc_id":"rule-001","source_page":3,"source_quote":"入口缺失应核查入口流水","confidence":1.0,"source_kind":"curated_triples"}
```

导入后状态为 `draft`。管理员审核通过后，系统才会写入 Neo4j。审核驳回的关系不会进入正式图谱。

旧的 `/api/graph/neo4j/add-entities` 接口已作为兼容入口保留，但行为改为导入草稿，不再直接写正式图谱。

## 自动抽取边界

默认关闭自动图谱抽取。以下内容禁止自动抽取正式关系：

- OCR 结果
- 扫描 PDF
- 表格密集文件
- 原始通行流水
- 大批量业务记录
- 未标注文档类型的普通上传文件

轻量关系抽取只适合规则清单、案例摘要、制度条款，并且必须先进入草稿状态。

## Visual RAG PoC

视觉检索接口位于：

- `POST /api/knowledge/visual-rag/index`
- `POST /api/knowledge/visual-rag/query`

当前 PoC 支持 PDF 页级索引：保存页码、页面图片、页面 hash 和文本预览。接口返回的是页面证据，后续可以将内部 scorer 替换为 ColPali 或 ColQwen 的多向量 late interaction 检索。

Visual RAG 适合找“哪一页可能有依据”，不替代结构化三元组，也不用于通行流水计算。
