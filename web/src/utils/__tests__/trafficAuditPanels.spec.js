import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

import { buildCaseAnalysis, buildReportMetrics, buildRouteSummary } from '../trafficAuditPanels.js'

const fixture = JSON.parse(
  readFileSync(resolve(process.cwd(), 'test/fixtures/traffic_audit/panel_demo_cases.json'), 'utf-8')
)

const run = () => {
  const [normalCase, riskCase] = fixture.cases

  const normalRoute = buildRouteSummary(normalCase.analysis_result.route)
  assert.equal(normalRoute.mainRoute, 'S02 → S04')
  assert.equal(normalRoute.confidence, 98)
  assert.match(normalRoute.description, /入口和出口事件完整/)

  const riskAnalysis = buildCaseAnalysis(riskCase)
  assert.equal(riskAnalysis.vehicle, 'TEST00156')
  assert.equal(riskAnalysis.anomalyCount, 1)
  assert.equal(riskAnalysis.relatedCases[0].title, '计费不一致 相似案例')

  const metrics = buildReportMetrics(riskCase.analysis_result.evidence)
  assert.deepEqual(metrics, [
    {
      type: 'fee_mismatch',
      label: '计费不一致',
      count: 1,
      percent: 100
    }
  ])
}

run()
