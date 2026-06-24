<script setup>
import { computed } from 'vue'

import { buildCaseAnalysis } from '@/utils/trafficAuditPanels'

const props = defineProps({
  caseData: {
    type: Object,
    required: true
  }
})

const analysis = computed(() => buildCaseAnalysis(props.caseData))
</script>

<template>
  <a-card title="案例分析" class="audit-panel">
    <template #extra>
      <a-tag color="purple">文本分析摘要</a-tag>
    </template>

    <div class="summary-grid">
      <a-statistic title="车辆" :value="analysis.vehicle" />
      <a-statistic title="通行节点" :value="analysis.passageCount" />
      <a-statistic title="异常证据" :value="analysis.anomalyCount" />
      <a-statistic title="综合评分" :value="analysis.score" suffix="/ 100" />
    </div>

    <div class="analysis-grid">
      <div>
        <h3>通行特征</h3>
        <a-list :data-source="analysis.features" bordered>
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta :title="item.title" :description="item.description" />
              <strong>{{ item.value }}</strong>
            </a-list-item>
          </template>
        </a-list>
      </div>

      <div>
        <h3>历史案例关联</h3>
        <a-list :data-source="analysis.relatedCases" bordered>
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta :title="item.id + ' ' + item.title" :description="item.description" />
            </a-list-item>
          </template>
        </a-list>
      </div>
    </div>
  </a-card>
</template>

<style lang="less" scoped>
.audit-panel {
  margin-bottom: 18px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 22px;
}

.summary-grid :deep(.ant-statistic) {
  padding: 16px;
  border: 1px solid var(--gray-200);
  border-radius: 8px;
  background: var(--main-10);
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

h3 {
  margin: 0 0 12px;
}

@media (max-width: 900px) {
  .summary-grid,
  .analysis-grid {
    grid-template-columns: 1fr;
  }
}
</style>
