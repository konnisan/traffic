<script setup>
import { computed, h, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { message, Modal } from 'ant-design-vue'
import { ArrowLeft, Play } from 'lucide-vue-next'

import { trafficAuditApi } from '@/apis'
import { useUserStore } from '@/stores/user'
import RouteRestorePanel from '@/components/traffic-audit/RouteRestorePanel.vue'
import CaseAnalysisPanel from '@/components/traffic-audit/CaseAnalysisPanel.vue'
import AuditReportPanel from '@/components/traffic-audit/AuditReportPanel.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const auditCase = ref(null)
const loading = ref(false)
const analyzing = ref(false)
const workflowRunning = ref(false)
const uploadType = ref('vehicles')
const uploadFile = ref(null)
const uploading = ref(false)
let pollTimer = null

const datasetOptions = [
  { label: '车辆档案 vehicles', value: 'vehicles' },
  { label: '收费交易 transactions', value: 'transactions' },
  { label: '通行事件 passages', value: 'passages' }
]

const statusLabels = {
  draft: '待上传数据',
  ready: '可分析',
  queued: '排队中',
  analyzing: '分析中',
  pending_review: '待复核',
  confirmed: '已确认',
  rejected: '已驳回',
  analysis_failed: '分析失败'
}

const canAnalyze = computed(() =>
  ['ready', 'analysis_failed', 'pending_review', 'confirmed', 'rejected'].includes(auditCase.value?.status)
)
const canRunWorkflow = computed(() => Boolean(auditCase.value?.analysis_result))
const isTaskRunning = computed(() => ['queued', 'analyzing'].includes(auditCase.value?.status))

async function loadCase() {
  loading.value = true
  try {
    auditCase.value = (await trafficAuditApi.getCase(route.params.caseId)).case
    if (isTaskRunning.value) startPolling()
  } catch (error) {
    message.error(error.message)
  } finally {
    loading.value = false
  }
}

function chooseFile(file) {
  uploadFile.value = file
  return false
}

async function uploadDataset() {
  if (!uploadFile.value) {
    message.warning('请选择数据文件')
    return
  }
  uploading.value = true
  try {
    auditCase.value = (await trafficAuditApi.uploadDataset(auditCase.value.id, uploadType.value, uploadFile.value)).case
    uploadFile.value = null
    message.success('数据已校验并导入')
  } catch (error) {
    message.error(error.message)
  } finally {
    uploading.value = false
  }
}

async function analyze() {
  analyzing.value = true
  try {
    auditCase.value = (await trafficAuditApi.analyzeCase(auditCase.value.id)).case
    startPolling()
  } catch (error) {
    message.error(error.message)
  } finally {
    analyzing.value = false
  }
}

async function runDifyReportDraft() {
  if (!canRunWorkflow.value) return
  workflowRunning.value = true
  try {
    auditCase.value = (await trafficAuditApi.runWorkflow(auditCase.value.id, 'audit_report_draft')).case
    startPolling()
    message.success('报告草稿工作流已启动')
  } catch (error) {
    message.error(error.message)
  } finally {
    workflowRunning.value = false
  }
}

function startPolling() {
  if (pollTimer) return
  pollTimer = window.setInterval(async () => {
    try {
      const task = (await trafficAuditApi.getTask(auditCase.value.id)).task
      if (task && ['success', 'failed', 'cancelled'].includes(task.status)) {
        window.clearInterval(pollTimer)
        pollTimer = null
        await loadCase()
      }
    } catch {
      window.clearInterval(pollTimer)
      pollTimer = null
    }
  }, 1500)
}

function review(decision) {
  let comment = ''
  Modal.confirm({
    title: decision === 'confirmed' ? '确认异常结论' : '驳回智能分析结论',
    content: () =>
      h('textarea', {
        class: 'ant-input',
        rows: 4,
        placeholder: '请输入复核意见（可选）',
        onInput: (event) => (comment = event.target.value)
      }),
    async onOk() {
      auditCase.value = (await trafficAuditApi.reviewCase(auditCase.value.id, { decision, comment })).case
      message.success('复核结论已保存')
    }
  })
}

async function downloadReport() {
  try {
    const response = await trafficAuditApi.downloadReport(auditCase.value.id)
    const url = URL.createObjectURL(await response.blob())
    const link = document.createElement('a')
    link.href = url
    link.download = `traffic-audit-${auditCase.value.id}.md`
    link.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    message.error(error.message)
  }
}

onMounted(loadCase)
onBeforeUnmount(() => pollTimer && window.clearInterval(pollTimer))
</script>

<template>
  <div v-if="auditCase" class="audit-detail">
    <header>
      <a-button type="text" @click="router.push('/audit')">
        <ArrowLeft :size="18" />
        返回
      </a-button>
      <div class="heading">
        <h1>{{ auditCase.title }}</h1>
        <p>
          {{ auditCase.plate_number }} |
          {{ dayjs(auditCase.started_at).format('YYYY-MM-DD HH:mm') }} 至
          {{ dayjs(auditCase.ended_at).format('YYYY-MM-DD HH:mm') }}
        </p>
      </div>
      <a-tag>{{ statusLabels[auditCase.status] || auditCase.status }}</a-tag>
    </header>

    <a-card class="dataset-card" title="样例数据">
      <template #extra>
        <a-space>
          <a-select v-model:value="uploadType" :options="datasetOptions" style="width: 220px" />
          <a-upload :before-upload="chooseFile" :show-upload-list="false" accept=".csv,.xlsx,.xlsm">
            <a-button>{{ uploadFile?.name || '选择文件' }}</a-button>
          </a-upload>
          <a-button :loading="uploading" @click="uploadDataset">导入</a-button>
        </a-space>
      </template>

      <div class="dataset-counts">
        <span v-for="option in datasetOptions" :key="option.value">
          {{ option.label }}
          <strong>{{ auditCase.dataset_summary[option.value] || 0 }}</strong>
        </span>
      </div>
      <p>上传后自动校验字段、标准化车牌和时间，并按 record_id 去重。</p>
    </a-card>

    <a-card class="analysis-card">
      <div class="analysis-action">
        <div>
          <h2>确定性稽核分析</h2>
          <p>路径还原、案例分析和报告草稿均在独立面板展示，不作为工具调用结果呈现。</p>
        </div>
        <a-button type="primary" :disabled="!canAnalyze" :loading="analyzing || isTaskRunning" @click="analyze">
          <Play :size="16" />
          开始分析
        </a-button>
      </div>
    </a-card>

    <template v-if="auditCase.analysis_result">
      <RouteRestorePanel :route="auditCase.analysis_result.route" />
      <CaseAnalysisPanel :case-data="auditCase" />
      <AuditReportPanel
        :report-markdown="auditCase.report_markdown"
        :evidence="auditCase.analysis_result.evidence"
        :workflow-disabled="!canRunWorkflow"
        :workflow-loading="workflowRunning"
        @download="downloadReport"
        @generate-dify="runDifyReportDraft"
      />

      <a-card v-if="auditCase.analysis_result.evidence.length" title="异常证据" class="audit-panel">
        <a-collapse>
          <a-collapse-panel v-for="(item, index) in auditCase.analysis_result.evidence" :key="index" :header="item.fact">
            <p><strong>异常类型：</strong>{{ item.anomaly_type }} <strong>风险等级：</strong>{{ item.severity }}</p>
            <p><strong>规则依据：</strong>{{ item.rule_basis }}</p>
            <p><strong>置信说明：</strong>{{ item.confidence_note }}</p>
            <p>
              <strong>源记录：</strong>
              {{ item.sources.map((source) => `${source.source_file}:${source.row_number}(${source.record_id})`).join('，') }}
            </p>
          </a-collapse-panel>
        </a-collapse>
      </a-card>

      <a-card v-if="auditCase.status === 'pending_review' && userStore.isAdmin" title="人工复核" class="audit-panel">
        <div class="review-actions">
          <p>确认或驳回后将记录复核人、意见和时间。未经人工确认不得作为正式结论。</p>
          <a-space>
            <a-button danger @click="review('rejected')">驳回结论</a-button>
            <a-button type="primary" @click="review('confirmed')">确认异常</a-button>
          </a-space>
        </div>
      </a-card>
    </template>
  </div>
  <div v-else class="loading">
    <a-spin :spinning="loading" />
  </div>
</template>

<style lang="less" scoped>
.audit-detail {
  max-width: 1180px;
  padding: 24px 32px 60px;
  margin: 0 auto;
}

header {
  display: flex;
  gap: 18px;
  align-items: center;
  margin-bottom: 20px;
}

.heading {
  flex: 1;
}

.heading h1 {
  margin: 0;
  font-size: 24px;
}

.heading p {
  margin: 4px 0 0;
  color: var(--gray-600);
}

.dataset-card,
.analysis-card,
.audit-panel {
  margin-bottom: 18px;
}

.dataset-counts {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  margin-bottom: 8px;
}

.dataset-counts span {
  color: var(--gray-600);
}

.dataset-counts strong {
  margin-left: 8px;
  color: var(--main-700);
}

.dataset-card p,
.analysis-action p,
.review-actions p {
  margin: 0;
  color: var(--gray-600);
}

.analysis-action,
.review-actions {
  display: flex;
  gap: 16px;
  align-items: center;
  justify-content: space-between;
}

.analysis-action h2 {
  margin: 0 0 6px;
}

.loading {
  display: grid;
  min-height: 60vh;
  place-items: center;
}

@media (max-width: 800px) {
  .audit-detail {
    padding: 18px;
  }

  header,
  .analysis-action,
  .review-actions {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
