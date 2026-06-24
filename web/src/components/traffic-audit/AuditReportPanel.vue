<script setup>
import { computed } from 'vue'
import { Download } from 'lucide-vue-next'

import { buildReportMetrics } from '@/utils/trafficAuditPanels'

const props = defineProps({
  reportMarkdown: {
    type: String,
    default: ''
  },
  evidence: {
    type: Array,
    default: () => []
  },
  workflowDisabled: {
    type: Boolean,
    default: false
  },
  workflowLoading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['download', 'generate-dify'])

const metrics = computed(() => buildReportMetrics(props.evidence))
</script>

<template>
  <a-card title="稽核报告生成" class="audit-panel">
    <template #extra>
      <a-space>
        <a-button :disabled="workflowDisabled" :loading="workflowLoading" @click="emit('generate-dify')">生成 Dify 草稿</a-button>
        <a-button @click="emit('download')">
          <Download :size="16" />
          下载 Markdown
        </a-button>
      </a-space>
    </template>

    <div class="report-grid">
      <div class="distribution">
        <h3>逃费类型分布分析</h3>
        <a-empty v-if="!metrics.length" description="当前案件未命中异常类型" />
        <div v-for="item in metrics" v-else :key="item.type" class="metric-row">
          <div>
            <strong>{{ item.label }}</strong>
            <span>{{ item.count }} 条，占比 {{ item.percent }}%</span>
          </div>
          <a-progress :percent="item.percent" size="small" />
        </div>
      </div>

      <div class="report-preview">
        <h3>报告草稿</h3>
        <pre>{{ reportMarkdown || '暂无报告草稿，请先运行确定性分析。' }}</pre>
      </div>
    </div>
  </a-card>
</template>

<style lang="less" scoped>
.audit-panel {
  margin-bottom: 18px;
}

.report-grid {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 18px;
}

.distribution,
.report-preview {
  padding: 16px;
  border: 1px solid var(--gray-200);
  border-radius: 8px;
  background: var(--gray-10);
}

h3 {
  margin: 0 0 14px;
}

.metric-row {
  margin-bottom: 16px;
}

.metric-row div {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
}

.metric-row span {
  color: var(--gray-600);
}

pre {
  max-height: 520px;
  padding: 16px;
  margin: 0;
  overflow: auto;
  border-left: 3px solid var(--main-300);
  background: var(--gray-25);
  font-family: inherit;
  line-height: 1.75;
  white-space: pre-wrap;
}

@media (max-width: 980px) {
  .report-grid {
    grid-template-columns: 1fr;
  }
}
</style>
