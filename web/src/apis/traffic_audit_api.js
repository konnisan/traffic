import { apiGet, apiPost } from './base'

export const trafficAuditApi = {
  listCases() {
    return apiGet('/api/audit/cases')
  },
  getCase(caseId) {
    return apiGet(`/api/audit/cases/${caseId}`)
  },
  createCase(payload) {
    return apiPost('/api/audit/cases', payload)
  },
  uploadDataset(caseId, datasetType, file) {
    const formData = new FormData()
    formData.append('dataset_type', datasetType)
    formData.append('file', file)
    return apiPost(`/api/audit/cases/${caseId}/datasets`, formData)
  },
  analyzeCase(caseId) {
    return apiPost(`/api/audit/cases/${caseId}/analyze`)
  },
  getTask(caseId) {
    return apiGet(`/api/audit/cases/${caseId}/task`)
  },
  reviewCase(caseId, payload) {
    return apiPost(`/api/audit/cases/${caseId}/review`, payload)
  },
  listWorkflows(caseId) {
    return apiGet(`/api/audit/cases/${caseId}/workflows`)
  },
  runWorkflow(caseId, workflowCode) {
    return apiPost(`/api/audit/cases/${caseId}/workflows/${workflowCode}/run`)
  },
  downloadReport(caseId) {
    return apiGet(`/api/audit/cases/${caseId}/report`, {}, true, 'blob')
  }
}
