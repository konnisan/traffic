<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { message } from 'ant-design-vue'

import HeaderComponent from '@/components/HeaderComponent.vue'
import { trafficAuditApi } from '@/apis'

const router = useRouter()
const loading = ref(false)
const creating = ref(false)
const modalOpen = ref(false)
const cases = ref([])
const form = reactive({ title: '', plate_number: '', timeRange: [] })

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

const columns = [
  { title: '案件名称', dataIndex: 'title', key: 'title' },
  { title: '车牌号', dataIndex: 'plate_number', key: 'plate_number', width: 140 },
  { title: '分析时间窗', key: 'period', width: 320 },
  { title: '状态', key: 'status', width: 130 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 190 }
]

async function loadCases() {
  loading.value = true
  try {
    cases.value = (await trafficAuditApi.listCases()).cases
  } catch (error) {
    message.error(error.message)
  } finally {
    loading.value = false
  }
}

async function createCase() {
  if (!form.title.trim() || !form.plate_number.trim() || form.timeRange.length !== 2) {
    message.warning('请填写案件名称、车牌号和分析时间窗')
    return
  }
  creating.value = true
  try {
    const response = await trafficAuditApi.createCase({
      title: form.title,
      plate_number: form.plate_number,
      started_at: dayjs(form.timeRange[0]).format('YYYY-MM-DDTHH:mm:ss'),
      ended_at: dayjs(form.timeRange[1]).format('YYYY-MM-DDTHH:mm:ss')
    })
    modalOpen.value = false
    form.title = ''
    form.plate_number = ''
    form.timeRange = []
    router.push(`/audit/${response.case.id}`)
  } catch (error) {
    message.error(error.message)
  } finally {
    creating.value = false
  }
}

onMounted(loadCases)
</script>

<template>
  <div class="audit-list layout-container">
    <HeaderComponent title="交通稽核" :loading="loading">
      <template #actions>
        <a-button type="primary" @click="modalOpen = true">新建案件</a-button>
      </template>
    </HeaderComponent>

    <div class="intro">
      <div>
        <h2>逃费路径还原</h2>
        <p>基于样例通行流水还原车辆路径，输出可追溯异常证据和待人工确认的报告草稿。</p>
        <p class="entry-tip">
          当前位置：<code>/audit</code>。点击案件行进入详情页 <code>/audit/:caseId</code>，完成分析后会显示“路径还原、案例分析、稽核报告生成”三个独立面板。
        </p>
      </div>
      <span>辅助研判，不自动定案</span>
    </div>

    <a-table
      :columns="columns"
      :data-source="cases"
      :loading="loading"
      row-key="id"
      :pagination="{ pageSize: 12 }"
      class="case-table"
      :custom-row="(record) => ({ onClick: () => router.push(`/audit/${record.id}`) })"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'period'">
          {{ dayjs(record.started_at).format('YYYY-MM-DD HH:mm') }} 至
          {{ dayjs(record.ended_at).format('YYYY-MM-DD HH:mm') }}
        </template>
        <template v-else-if="column.key === 'status'">
          <a-tag>{{ statusLabels[record.status] || record.status }}</a-tag>
        </template>
        <template v-else-if="column.key === 'created_at'">
          {{ dayjs(record.created_at).format('YYYY-MM-DD HH:mm') }}
        </template>
      </template>
    </a-table>

    <a-modal
      :open="modalOpen"
      title="新建交通稽核案件"
      :confirm-loading="creating"
      @ok="createCase"
      @cancel="modalOpen = false"
    >
      <a-form layout="vertical">
        <a-form-item label="案件名称" required>
          <a-input v-model:value="form.title" placeholder="例如：鄂A12345 通行异常核查" />
        </a-form-item>
        <a-form-item label="疑似车辆" required>
          <a-input v-model:value="form.plate_number" placeholder="车牌号" />
        </a-form-item>
        <a-form-item label="分析时间窗" required>
          <a-range-picker v-model:value="form.timeRange" show-time style="width: 100%" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<style lang="less" scoped>
.audit-list {
  padding: 24px 32px;
}

.intro {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  margin-bottom: 20px;
  border: 1px solid var(--gray-200);
  border-radius: 10px;
  background: var(--main-10);

  h2 {
    margin: 0 0 6px;
    color: var(--gray-900);
  }

  p {
    margin: 0;
    color: var(--gray-600);
  }

  .entry-tip {
    margin-top: 8px;
    color: var(--gray-700);
  }

  code {
    padding: 1px 5px;
    border-radius: 4px;
    background: var(--gray-100);
    color: var(--main-700);
  }

  span {
    color: var(--color-warning-700);
  }
}

.case-table :deep(.ant-table-row) {
  cursor: pointer;
}
</style>
