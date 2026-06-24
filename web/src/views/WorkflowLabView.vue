<script setup>
import { computed, ref } from 'vue'
import { ArrowDown, Bot, Database, FileText, GitBranch, Play, Plus, RotateCcw, Settings2, Trash2 } from 'lucide-vue-next'
import { message } from 'ant-design-vue'

const componentCatalog = [
  {
    type: 'traffic.parse_files',
    name: '样例文件解析',
    category: '文件处理',
    icon: FileText,
    description: '解析车辆、交易、通行事件 CSV/XLSX，输出标准记录。',
    inputs: ['uploaded_files'],
    outputs: ['vehicles', 'transactions', 'passages'],
    config: { accepted: 'csv,xlsx', dedupe_by: 'record_id' }
  },
  {
    type: 'traffic.restore_route',
    name: '路径还原',
    category: '交通稽核',
    icon: GitBranch,
    description: '按时间和业务序号还原入口、门架、出口通行链。',
    inputs: ['passages'],
    outputs: ['route'],
    config: { sort_by: 'event_time', keep_source_refs: true }
  },
  {
    type: 'traffic.detect_anomaly',
    name: '异常规则检测',
    category: '交通稽核',
    icon: Settings2,
    description: '执行入口缺失、时序冲突、路径断点、费用不一致规则。',
    inputs: ['route', 'transactions'],
    outputs: ['evidence'],
    config: { rules: ['missing_endpoint', 'time_conflict', 'route_discontinuity', 'fee_mismatch'] }
  },
  {
    type: 'rag.policy_retrieve',
    name: '政策依据检索',
    category: '知识库',
    icon: Database,
    description: '从政策、制度、规则和案例知识库检索依据。',
    inputs: ['evidence'],
    outputs: ['policy_basis'],
    config: { top_k: 5, source: 'traffic_policy_dataset' }
  },
  {
    type: 'graph.query_relations',
    name: '图谱关系查询',
    category: '知识图谱',
    icon: GitBranch,
    description: '查询规则、异常类型、证据项和案例之间的结构关系。',
    inputs: ['evidence'],
    outputs: ['relation_paths'],
    config: { relation_scope: 'approved_triples' }
  },
  {
    type: 'agent.explain_case',
    name: '智能体解释',
    category: '智能体',
    icon: Bot,
    description: '根据结构化证据和依据生成可追问的解释，不改变事实结论。',
    inputs: ['evidence', 'policy_basis'],
    outputs: ['case_explanation'],
    config: { mode: 'assist_only', allow_write_conclusion: false }
  },
  {
    type: 'dify.audit_report',
    name: 'Dify 报告草稿',
    category: 'Dify',
    icon: Bot,
    description: '调用 Dify Workflow 生成报告草稿，只保存为 draft。',
    inputs: ['evidence', 'policy_basis', 'case_explanation'],
    outputs: ['report_markdown'],
    config: { workflow_code: 'audit_report_draft' }
  }
]

const defaultWorkflow = [
  'traffic.parse_files',
  'traffic.restore_route',
  'traffic.detect_anomaly',
  'rag.policy_retrieve',
  'dify.audit_report'
]

const selectedTypes = ref([...defaultWorkflow])
const selectedNodeId = ref(null)
const runState = ref('idle')

const workflowNodes = computed(() =>
  selectedTypes.value.map((type, index) => ({
    id: `${type}-${index}`,
    order: index + 1,
    ...componentCatalog.find((item) => item.type === type)
  }))
)

const selectedNode = computed(() => workflowNodes.value.find((node) => node.id === selectedNodeId.value) || workflowNodes.value[0])

const groupedComponents = computed(() => {
  const groups = {}
  for (const item of componentCatalog) {
    groups[item.category] ||= []
    groups[item.category].push(item)
  }
  return groups
})

const workflowJson = computed(() => ({
  name: '交通稽核实验工作流',
  mode: 'dag',
  nodes: workflowNodes.value.map((node) => ({
    id: `node_${node.order}`,
    type: node.type,
    name: node.name,
    inputs: node.inputs,
    outputs: node.outputs,
    config: node.config
  })),
  edges: workflowNodes.value.slice(0, -1).map((node, index) => ({
    from: `node_${node.order}`,
    to: `node_${index + 2}`
  })),
  safety: {
    deterministic_facts_first: true,
    llm_outputs_are_draft_only: true,
    human_review_required: true
  }
}))

const runPreview = computed(() =>
  workflowNodes.value.map((node, index) => ({
    node: node.name,
    status: runState.value === 'success' ? 'success' : index === 0 && runState.value === 'running' ? 'running' : 'pending',
    output: node.outputs.join(', ')
  }))
)

function addComponent(type) {
  selectedTypes.value.push(type)
  message.success('组件已加入实验流程')
}

function removeNode(index) {
  selectedTypes.value.splice(index, 1)
  selectedNodeId.value = null
}

function moveNode(index, offset) {
  const target = index + offset
  if (target < 0 || target >= selectedTypes.value.length) return
  const current = selectedTypes.value[index]
  selectedTypes.value[index] = selectedTypes.value[target]
  selectedTypes.value[target] = current
}

function resetWorkflow() {
  selectedTypes.value = [...defaultWorkflow]
  selectedNodeId.value = null
  runState.value = 'idle'
}

function simulateRun() {
  runState.value = 'running'
  window.setTimeout(() => {
    runState.value = 'success'
    message.success('实验工作流模拟运行完成')
  }, 600)
}
</script>

<template>
  <div class="workflow-lab">
    <header class="lab-header">
      <div>
        <a-tag color="blue">实验页</a-tag>
        <h1>组件式智能体工作流实验</h1>
        <p>这个页面不影响现有交通稽核流程，用来验证 Haystack 式组件选择、编排和运行记录设计。</p>
      </div>
      <a-space>
        <a-button @click="resetWorkflow">
          <RotateCcw :size="16" />
          重置
        </a-button>
        <a-button type="primary" @click="simulateRun">
          <Play :size="16" />
          模拟运行
        </a-button>
      </a-space>
    </header>

    <div class="lab-layout">
      <aside class="component-panel">
        <h2>组件库</h2>
        <div v-for="(items, category) in groupedComponents" :key="category" class="component-group">
          <h3>{{ category }}</h3>
          <button v-for="item in items" :key="item.type" class="component-card" @click="addComponent(item.type)">
            <component :is="item.icon" :size="18" />
            <span>
              <strong>{{ item.name }}</strong>
              <small>{{ item.description }}</small>
            </span>
            <Plus :size="16" />
          </button>
        </div>
      </aside>

      <main class="workflow-canvas">
        <div class="canvas-title">
          <h2>流程编排</h2>
          <span>当前 {{ workflowNodes.length }} 个节点</span>
        </div>

        <a-empty v-if="!workflowNodes.length" description="请从左侧选择组件" />
        <div v-else class="node-list">
          <template v-for="(node, index) in workflowNodes" :key="node.id">
            <div class="workflow-node" :class="{ active: selectedNode?.id === node.id }" @click="selectedNodeId = node.id">
              <div class="node-icon">
                <component :is="node.icon" :size="20" />
              </div>
              <div class="node-body">
                <div class="node-head">
                  <strong>{{ node.order }}. {{ node.name }}</strong>
                  <a-tag>{{ node.category }}</a-tag>
                </div>
                <p>{{ node.description }}</p>
                <div class="io-line">
                  <span>输入：{{ node.inputs.join(', ') }}</span>
                  <span>输出：{{ node.outputs.join(', ') }}</span>
                </div>
              </div>
              <a-space>
                <a-button size="small" :disabled="index === 0" @click.stop="moveNode(index, -1)">上移</a-button>
                <a-button size="small" :disabled="index === workflowNodes.length - 1" @click.stop="moveNode(index, 1)">下移</a-button>
                <a-button size="small" danger @click.stop="removeNode(index)">
                  <Trash2 :size="14" />
                </a-button>
              </a-space>
            </div>
            <div v-if="index < workflowNodes.length - 1" class="edge-arrow">
              <ArrowDown :size="18" />
            </div>
          </template>
        </div>
      </main>

      <aside class="detail-panel">
        <h2>节点配置</h2>
        <template v-if="selectedNode">
          <a-descriptions :column="1" size="small" bordered>
            <a-descriptions-item label="类型">{{ selectedNode.type }}</a-descriptions-item>
            <a-descriptions-item label="输入">{{ selectedNode.inputs.join(', ') }}</a-descriptions-item>
            <a-descriptions-item label="输出">{{ selectedNode.outputs.join(', ') }}</a-descriptions-item>
          </a-descriptions>

          <h3>配置预览</h3>
          <pre>{{ JSON.stringify(selectedNode.config, null, 2) }}</pre>
        </template>

        <h2>运行预览</h2>
        <a-list :data-source="runPreview" bordered size="small">
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta :title="item.node" :description="`输出：${item.output}`" />
              <a-tag :color="item.status === 'success' ? 'green' : item.status === 'running' ? 'blue' : 'default'">
                {{ item.status }}
              </a-tag>
            </a-list-item>
          </template>
        </a-list>

        <h2>定义 JSON</h2>
        <pre>{{ JSON.stringify(workflowJson, null, 2) }}</pre>
      </aside>
    </div>
  </div>
</template>

<style lang="less" scoped>
.workflow-lab {
  min-height: 100%;
  padding: 24px 28px 40px;
  background: var(--gray-10);
}

.lab-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 20px;
}

.lab-header h1 {
  margin: 12px 0 6px;
  font-size: 26px;
}

.lab-header p {
  margin: 0;
  color: var(--gray-600);
}

.lab-layout {
  display: grid;
  grid-template-columns: 310px minmax(420px, 1fr) 360px;
  gap: 18px;
  align-items: start;
}

.component-panel,
.workflow-canvas,
.detail-panel {
  padding: 18px;
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  background: var(--gray-0);
}

h2 {
  margin: 0 0 14px;
  font-size: 18px;
}

h3 {
  margin: 16px 0 10px;
  color: var(--gray-700);
  font-size: 14px;
}

.component-card {
  display: grid;
  grid-template-columns: 22px minmax(0, 1fr) 18px;
  gap: 10px;
  align-items: center;
  width: 100%;
  padding: 12px;
  margin-bottom: 8px;
  border: 1px solid var(--gray-200);
  border-radius: 10px;
  background: var(--gray-10);
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.component-card:hover {
  border-color: var(--main-200);
  background: var(--main-10);
}

.component-card strong,
.component-card small {
  display: block;
}

.component-card small {
  margin-top: 3px;
  color: var(--gray-600);
  line-height: 1.5;
}

.canvas-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.canvas-title span {
  color: var(--gray-600);
}

.workflow-node {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 14px;
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  background: var(--gray-10);
  cursor: pointer;
}

.workflow-node.active {
  border-color: var(--main-300);
  background: var(--main-10);
}

.node-icon {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  border-radius: 10px;
  background: var(--main-50);
  color: var(--main-700);
}

.node-head {
  display: flex;
  gap: 10px;
  align-items: center;
}

.node-body p {
  margin: 6px 0;
  color: var(--gray-600);
}

.io-line {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: var(--gray-700);
  font-size: 12px;
}

.edge-arrow {
  display: flex;
  justify-content: center;
  padding: 6px 0;
  color: var(--main-500);
}

pre {
  max-height: 260px;
  padding: 12px;
  overflow: auto;
  border: 1px solid var(--gray-200);
  border-radius: 8px;
  background: var(--gray-25);
  color: var(--gray-800);
  font-size: 12px;
}

.detail-panel h2:not(:first-child) {
  margin-top: 18px;
}

@media (max-width: 1280px) {
  .lab-layout {
    grid-template-columns: 1fr;
  }
}
</style>
