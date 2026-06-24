export const anomalyLabels = {
  missing_endpoint: '入口/出口缺失',
  time_conflict: '时序冲突',
  route_discontinuity: '路径不连续',
  fee_mismatch: '计费不一致'
}

export const severityLabels = {
  high: '高风险',
  medium: '中风险',
  low: '低风险'
}

export function buildRouteSummary(route = []) {
  if (!route.length) {
    return {
      mainRoute: '暂无路径',
      confidence: 0,
      startPoint: '-',
      endPoint: '-',
      description: '尚未完成路径还原。'
    }
  }

  const first = route[0]
  const last = route[route.length - 1]
  const gantryCount = route.filter((item) => item.event_type === 'gantry').length
  const hasEntry = first.event_type === 'entry'
  const hasExit = last.event_type === 'exit'
  const continuityHits = route.slice(0, -1).filter((item, index) => {
    const expected = item.next_location_code
    return expected && expected !== route[index + 1]?.location_code
  }).length
  const confidence = Math.max(45, 98 - (!hasEntry ? 18 : 0) - (!hasExit ? 18 : 0) - continuityHits * 12)

  return {
    mainRoute: `${first.location_code} → ${last.location_code}`,
    confidence,
    startPoint: first.location_code,
    endPoint: last.location_code,
    description: `共还原 ${route.length} 个通行节点，其中门架 ${gantryCount} 个。${
      hasEntry && hasExit ? '入口和出口事件完整。' : '入口或出口事件不完整，需人工复核。'
    }`
  }
}

export function buildCaseAnalysis(caseData) {
  const result = caseData?.analysis_result || {}
  const route = result.route || []
  const evidence = result.evidence || []
  const anomalyTypes = [...new Set(evidence.map((item) => item.anomaly_type))]
  const highRiskCount = evidence.filter((item) => item.severity === 'high').length
  const confidence = Math.max(0, 100 - evidence.length * 10 - highRiskCount * 6)
  const first = route[0]
  const last = route[route.length - 1]

  return {
    vehicle: caseData?.plate_number || '-',
    passageCount: route.length,
    anomalyCount: evidence.length,
    score: confidence,
    features: [
      {
        title: '通行链完整性',
        value: first?.event_type === 'entry' && last?.event_type === 'exit' ? '入口出口完整' : '入口或出口缺失',
        description: first && last ? `${first.location_code} 至 ${last.location_code}` : '暂无路径数据'
      },
      {
        title: '异常类型',
        value: anomalyTypes.length ? anomalyTypes.map((type) => anomalyLabels[type] || type).join('、') : '未命中异常',
        description: evidence.length ? `共 ${evidence.length} 条证据需复核` : '当前规则未发现异常证据'
      },
      {
        title: '证据溯源',
        value: evidence.every((item) => item.sources?.length) ? '来源完整' : '存在缺失',
        description: '证据项需能定位到源文件、行号和原始记录 ID'
      }
    ],
    relatedCases: anomalyTypes.length
      ? anomalyTypes.map((type, index) => ({
          id: `SIM-${String(index + 1).padStart(3, '0')}`,
          title: `${anomalyLabels[type] || type} 相似案例`,
          description: '用于页面演示的相似案例摘要，正式版本应接入案例库检索。'
        }))
      : [
          {
            id: 'SIM-000',
            title: '暂无相似异常案例',
            description: '当前样本未命中一期规则异常。'
          }
        ]
  }
}

export function buildReportMetrics(evidence = []) {
  const counts = evidence.reduce((acc, item) => {
    const key = item.anomaly_type || 'unknown'
    acc[key] = (acc[key] || 0) + 1
    return acc
  }, {})
  const total = Object.values(counts).reduce((sum, count) => sum + count, 0)

  return Object.entries(counts).map(([type, count]) => ({
    type,
    label: anomalyLabels[type] || type,
    count,
    percent: total ? Math.round((count / total) * 100) : 0
  }))
}
