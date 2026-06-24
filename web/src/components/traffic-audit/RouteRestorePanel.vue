<script setup>
import { computed } from 'vue'
import dayjs from 'dayjs'

import { buildRouteSummary } from '@/utils/trafficAuditPanels'

const props = defineProps({
  route: {
    type: Array,
    default: () => []
  }
})

const summary = computed(() => buildRouteSummary(props.route))

const locationCoords = {
  S01: { x: 10, y: 72 },
  G01: { x: 32, y: 58 },
  G02: { x: 55, y: 42 },
  S03: { x: 84, y: 28 },
  S02: { x: 12, y: 28 },
  G03: { x: 34, y: 34 },
  G04: { x: 58, y: 52 },
  S04: { x: 84, y: 68 },
  S05: { x: 14, y: 82 },
  G05: { x: 36, y: 72 },
  G06: { x: 58, y: 58 },
  S09: { x: 86, y: 44 },
  S10: { x: 16, y: 40 },
  G10: { x: 40, y: 36 },
  G11: { x: 62, y: 46 },
  S12: { x: 86, y: 58 }
}

const mapPoints = computed(() =>
  props.route.map((item, index) => {
    const fallbackStep = props.route.length > 1 ? 76 / (props.route.length - 1) : 0
    const fallback = {
      x: 12 + fallbackStep * index,
      y: 46 + (index % 2 === 0 ? -10 : 10)
    }
    return {
      ...item,
      ...(locationCoords[item.location_code] || fallback)
    }
  })
)

const polylinePoints = computed(() => mapPoints.value.map((item) => `${item.x},${item.y}`).join(' '))
</script>

<template>
  <a-card title="路径还原" class="audit-panel">
    <template #extra>
      <a-tag color="blue">按时间线还原</a-tag>
    </template>

    <div class="route-grid">
      <div class="route-map">
        <div class="map-title">
          <strong>路径示意地图</strong>
          <span>站点/门架编码示意，不代表真实地理坐标</span>
        </div>
        <svg viewBox="0 0 100 100" role="img" aria-label="路径还原示意地图">
          <defs>
            <pattern id="audit-map-grid" width="12" height="12" patternUnits="userSpaceOnUse">
              <path d="M 12 0 L 0 0 0 12" fill="none" stroke="currentColor" stroke-width="0.25" />
            </pattern>
          </defs>
          <rect x="0" y="0" width="100" height="100" rx="4" class="map-bg" />
          <path d="M4 78 C22 70 34 68 48 58 S75 43 96 32" class="map-road road-a" />
          <path d="M7 26 C28 31 39 36 52 48 S75 67 95 72" class="map-road road-b" />
          <path d="M18 92 C31 73 44 56 58 38 S76 18 92 10" class="map-road road-c" />
          <polyline v-if="mapPoints.length > 1" :points="polylinePoints" class="route-line" />
          <g v-for="(item, index) in mapPoints" :key="item.record_id">
            <circle :cx="item.x" :cy="item.y" r="3.6" :class="['route-node', item.event_type]" />
            <text :x="item.x" :y="item.y - 6" text-anchor="middle" class="route-label">{{ item.location_code }}</text>
            <text :x="item.x" :y="item.y + 8.8" text-anchor="middle" class="route-index">{{ index + 1 }}</text>
          </g>
        </svg>
      </div>

      <div class="route-overview">
        <a-statistic title="主路径" :value="summary.mainRoute" />
        <a-progress :percent="summary.confidence" size="small" />
        <p>{{ summary.description }}</p>
      </div>

      <div class="route-points">
        <a-descriptions :column="1" size="small">
          <a-descriptions-item label="起点">{{ summary.startPoint }}</a-descriptions-item>
          <a-descriptions-item label="终点">{{ summary.endPoint }}</a-descriptions-item>
          <a-descriptions-item label="节点数">{{ route.length }}</a-descriptions-item>
        </a-descriptions>
      </div>
    </div>

    <a-timeline class="route-timeline">
      <a-timeline-item v-for="item in route" :key="item.record_id">
        <div class="timeline-row">
          <strong>{{ item.location_code }}</strong>
          <a-tag>{{ item.event_type }}</a-tag>
          <span>{{ dayjs(item.event_time).format('YYYY-MM-DD HH:mm:ss') }}</span>
        </div>
        <p>来源：{{ item.source.source_file }} 第 {{ item.source.row_number }} 行，记录 {{ item.source.record_id }}</p>
      </a-timeline-item>
    </a-timeline>
  </a-card>
</template>

<style lang="less" scoped>
.audit-panel {
  margin-bottom: 18px;
}

.route-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.9fr) 240px;
  gap: 18px;
  margin-bottom: 24px;
}

.route-map,
.route-overview,
.route-points {
  padding: 16px;
  border: 1px solid var(--gray-200);
  border-radius: 8px;
  background: var(--gray-10);
}

.map-title {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.map-title span {
  color: var(--gray-600);
  font-size: 12px;
}

.route-map svg {
  display: block;
  width: 100%;
  min-height: 260px;
  color: var(--gray-200);
  border: 1px solid var(--gray-200);
  border-radius: 8px;
  background: var(--main-5);
}

.map-bg {
  fill: url('#audit-map-grid');
}

.map-road {
  fill: none;
  stroke: var(--gray-300);
  stroke-linecap: round;
}

.road-a {
  stroke-width: 1.7;
}

.road-b {
  stroke-width: 1.3;
}

.road-c {
  stroke-width: 1;
  stroke-dasharray: 3 2;
}

.route-line {
  fill: none;
  stroke: var(--main-600);
  stroke-width: 2.4;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.route-node {
  stroke: var(--main-0);
  stroke-width: 1.2;
}

.route-node.entry {
  fill: var(--color-success-500);
}

.route-node.gantry {
  fill: var(--color-info-500);
}

.route-node.exit {
  fill: var(--color-warning-500);
}

.route-label {
  fill: var(--gray-900);
  font-size: 4px;
  font-weight: 600;
}

.route-index {
  fill: var(--main-0);
  font-size: 3.2px;
  font-weight: 700;
}

.route-overview p {
  margin: 10px 0 0;
  color: var(--gray-600);
}

.route-timeline {
  margin-top: 4px;
}

.timeline-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.route-timeline p {
  margin: 4px 0 0;
  color: var(--gray-600);
}

@media (max-width: 900px) {
  .route-grid {
    grid-template-columns: 1fr;
  }
}
</style>
