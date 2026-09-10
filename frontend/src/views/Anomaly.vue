<template>
  <div class="anomaly">
    <el-card shadow="never" class="control-card">
      <div class="control-row">
        <span class="control-label">选择作业批次 (job_id)：</span>
        <el-select
          v-model="selectedJob"
          placeholder="请选择 job_id"
          style="width: 220px"
          :loading="jobsLoading"
          @change="onJobChange"
        >
          <el-option v-for="id in jobIds" :key="id" :label="'job_' + id" :value="id" />
        </el-select>
        <el-button type="primary" :loading="loading" :disabled="selectedJob === null" @click="detect">
          开始检测
        </el-button>
        <template v-if="result">
          <span class="level-label">预警等级：</span>
          <el-tag size="large" effect="dark" :type="levelTagType">{{ result.level }}</el-tag>
          <el-tag v-if="result.anomaly_indices && result.anomaly_indices.length" type="danger" effect="plain">
            异常点 {{ result.anomaly_indices.length }} 个
          </el-tag>
        </template>
      </div>
    </el-card>

    <el-card shadow="never" v-loading="loading">
      <template #header>
        <span class="card-title">熔池温度 / 氧含量时序</span>
        <span class="hint">红色半透明区间为异常区间，黄色虚线为 3σ 上下限</span>
      </template>
      <div ref="chartRef" class="chart"></div>
      <el-empty v-if="!result" description="请选择 job_id 并点击「开始检测」" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { getJobs, detectAnomaly } from '../api'

const levelTypeMap = { 正常: 'success', 注意: 'warning', 告警: 'danger' }

const jobIds = ref([])
const jobsLoading = ref(false)
const selectedJob = ref(null)
const loading = ref(false)
const result = ref(null)
const chartRef = ref(null)
let chart = null

const levelTagType = ref('success')

async function loadJobs() {
  jobsLoading.value = true
  try {
    const res = await getJobs()
    jobIds.value = res.data.job_ids || []
  } catch (err) {
    const msg = err?.response?.data?.detail || err.message || '获取 job 列表失败'
    ElMessage.error(String(msg))
  } finally {
    jobsLoading.value = false
  }
}

function onJobChange() {
  // 切换 job 后清空旧结果
  result.value = null
}

async function detect() {
  if (selectedJob.value === null) {
    ElMessage.warning('请先选择 job_id')
    return
  }
  loading.value = true
  try {
    const res = await detectAnomaly(selectedJob.value)
    result.value = res.data
    levelTagType.value = levelTypeMap[res.data.level] || 'info'
    await nextTick()
    renderChart(res.data)
  } catch (err) {
    const msg = err?.response?.data?.detail || err.message || '异常检测请求失败'
    ElMessage.error(String(msg))
  } finally {
    loading.value = false
  }
}

function renderChart(data) {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value)
  }

  const areas = (data.intervals || []).map(([s, e]) => [
    { xAxis: s, itemStyle: { color: 'rgba(245,108,108,0.18)' } },
    { xAxis: e },
  ])

  const option = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['熔池温度 (°C)', '氧含量 (ppm)'] },
    grid: { left: 60, right: 60, top: 50, bottom: 40 },
    xAxis: {
      type: 'category',
      name: 'time_step',
      data: data.time_step,
    },
    yAxis: [
      { type: 'value', name: '温度 (°C)', scale: true },
      { type: 'value', name: '氧含量 (ppm)', scale: true },
    ],
    series: [
      {
        name: '熔池温度 (°C)',
        type: 'line',
        data: data.melt_pool_temp_C,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { width: 2 },
        itemStyle: { color: '#409eff' },
        markArea: {
          silent: true,
          data: areas,
        },
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { type: 'dashed', color: '#e6a23c', width: 1.5 },
          label: { formatter: '{b}', color: '#e6a23c' },
          data: [
            { yAxis: data.threshold_upper, name: '3σ上限' },
            { yAxis: data.threshold_lower, name: '3σ下限' },
          ],
        },
      },
      {
        name: '氧含量 (ppm)',
        type: 'line',
        yAxisIndex: 1,
        data: data.oxygen_ppm,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 1.5 },
        itemStyle: { color: '#67c23a' },
      },
    ],
  }

  chart.setOption(option, true)
}

function handleResize() {
  if (chart) chart.resize()
}

onMounted(() => {
  loadJobs()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<style scoped>
.control-card {
  margin-bottom: 20px;
}
.control-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.control-label {
  color: #606266;
}
.level-label {
  color: #606266;
}
.card-title {
  font-weight: 600;
}
.hint {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
  font-weight: normal;
}
.chart {
  width: 100%;
  height: 480px;
}
</style>
