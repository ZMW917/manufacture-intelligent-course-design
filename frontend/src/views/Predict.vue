<template>
  <div class="predict">
    <el-row :gutter="20">
      <el-col :span="10">
        <el-card shadow="never">
          <template #header><span class="card-title">工艺参数输入</span></template>
          <el-form label-width="140px" label-position="left">
            <el-form-item label="激光功率 (W)">
              <el-input-number v-model="form.laser_power_W" :min="0" :step="10" :precision="0" />
            </el-form-item>
            <el-form-item label="扫描速度 (mm/s)">
              <el-input-number v-model="form.scan_speed_mm_s" :min="0" :step="50" :precision="0" />
            </el-form-item>
            <el-form-item label="层厚 (μm)">
              <el-input-number v-model="form.layer_thickness_um" :min="0" :step="5" :precision="0" />
            </el-form-item>
            <el-form-item label="扫描间距 (μm)">
              <el-input-number v-model="form.hatch_spacing_um" :min="0" :step="5" :precision="0" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="loading" @click="doPredict">
                开始预测
              </el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card shadow="never" v-loading="loading">
          <template #header><span class="card-title">预测结果</span></template>

          <template v-if="result">
            <el-descriptions :column="1" border class="desc-block">
              <el-descriptions-item label="能量密度 (J/mm³)">
                {{ result.energy_density_J_mm3.toFixed(4) }}
              </el-descriptions-item>
            </el-descriptions>

            <el-divider content-position="left">RF / SVR 预测对比</el-divider>
            <el-table :data="comparisonRows" border size="small">
              <el-table-column prop="metric" label="指标" width="120" />
              <el-table-column prop="rf" label="随机森林 (RF)" />
              <el-table-column prop="svr" label="支持向量回归 (SVR)" />
            </el-table>

            <el-divider content-position="left">特征重要性</el-divider>
            <el-table :data="importanceRows" border size="small">
              <el-table-column prop="name" label="特征" />
              <el-table-column label="重要性" min-width="180">
                <template #default="{ row }">
                  <el-progress
                    :percentage="Math.round(row.value * 100)"
                    :stroke-width="12"
                    color="#409eff"
                  />
                </template>
              </el-table-column>
            </el-table>
          </template>

          <el-empty v-else description="请录入工艺参数后点击「开始预测」" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { predict } from '../api'

const featureNameMap = {
  laser_power_W: '激光功率 (W)',
  scan_speed_mm_s: '扫描速度 (mm/s)',
  layer_thickness_um: '层厚 (μm)',
  hatch_spacing_um: '扫描间距 (μm)',
}

const form = reactive({
  laser_power_W: 200,
  scan_speed_mm_s: 1000,
  layer_thickness_um: 30,
  hatch_spacing_um: 80,
})

const loading = ref(false)
const result = ref(null)

const comparisonRows = computed(() => {
  if (!result.value) return []
  const r = result.value
  return [
    { metric: '致密度', rf: (r.density_rf * 100).toFixed(2) + '%', svr: (r.density_svr * 100).toFixed(2) + '%' },
    { metric: '孔隙率', rf: (r.porosity_rf * 100).toFixed(2) + '%', svr: (r.porosity_svr * 100).toFixed(2) + '%' },
  ]
})

const importanceRows = computed(() => {
  if (!result.value || !result.value.feature_importances) return []
  return Object.entries(result.value.feature_importances).map(([k, v]) => ({
    name: featureNameMap[k] || k,
    value: v,
  }))
})

async function doPredict() {
  loading.value = true
  try {
    const res = await predict({ ...form })
    result.value = res.data
  } catch (err) {
    const msg = err?.response?.data?.detail || err.message || '预测请求失败'
    ElMessage.error(String(msg))
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.laser_power_W = 200
  form.scan_speed_mm_s = 1000
  form.layer_thickness_um = 30
  form.hatch_spacing_um = 80
  result.value = null
}
</script>

<style scoped>
.card-title {
  font-weight: 600;
}
.desc-block {
  margin-bottom: 12px;
}
</style>
