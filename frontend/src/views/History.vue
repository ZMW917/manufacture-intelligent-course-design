<template>
  <div class="history">
    <el-card shadow="never" class="table-card">
      <template #header><span class="card-title">预测历史记录</span></template>
      <el-table v-loading="predLoading" :data="predItems" border stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="laser_power_W" label="激光功率 (W)" />
        <el-table-column label="预测致密度">
          <template #default="{ row }">{{ (row.density_pred * 100).toFixed(2) }}%</template>
        </el-table-column>
        <el-table-column label="预测孔隙率">
          <template #default="{ row }">{{ (row.porosity_pred * 100).toFixed(2) }}%</template>
        </el-table-column>
        <el-table-column prop="model_type" label="模型" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="row.model_type === 'RF' ? 'primary' : 'success'">
              {{ row.model_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
      </el-table>
      <el-pagination
        class="pagination"
        background
        layout="total, prev, pager, next"
        :total="predTotal"
        :page-size="pageSize"
        :current-page="predPage"
        @current-change="onPredPageChange"
      />
    </el-card>

    <el-card shadow="never" class="table-card">
      <template #header><span class="card-title">图像识别记录</span></template>
      <el-table v-loading="imgLoading" :data="imgItems" border stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="image_name" label="图像名称" />
        <el-table-column prop="quality_label" label="标签编号" width="100" />
        <el-table-column prop="label_name" label="分类结果" width="140">
          <template #default="{ row }">
            <el-tag size="small" :type="labelTagType(row.quality_label)">{{ row.label_name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="置信度" width="140">
          <template #default="{ row }">{{ (row.confidence * 100).toFixed(2) }}%</template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
      </el-table>
      <el-pagination
        class="pagination"
        background
        layout="total, prev, pager, next"
        :total="imgTotal"
        :page-size="pageSize"
        :current-page="imgPage"
        @current-change="onImgPageChange"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getPredictionHistory, getImageHistory } from '../api'

const pageSize = 10

const predLoading = ref(false)
const predItems = ref([])
const predTotal = ref(0)
const predPage = ref(1)

const imgLoading = ref(false)
const imgItems = ref([])
const imgTotal = ref(0)
const imgPage = ref(1)

function labelTagType(label) {
  const map = { 0: 'success', 1: 'warning', 2: 'danger' }
  return map[label] || 'info'
}

async function loadPredictions() {
  predLoading.value = true
  try {
    const offset = (predPage.value - 1) * pageSize
    const res = await getPredictionHistory(pageSize, offset)
    predItems.value = res.data.items || []
    predTotal.value = res.data.total || 0
  } catch (err) {
    const msg = err?.response?.data?.detail || err.message || '获取预测历史失败'
    ElMessage.error(String(msg))
  } finally {
    predLoading.value = false
  }
}

async function loadImages() {
  imgLoading.value = true
  try {
    const offset = (imgPage.value - 1) * pageSize
    const res = await getImageHistory(pageSize, offset)
    imgItems.value = res.data.items || []
    imgTotal.value = res.data.total || 0
  } catch (err) {
    const msg = err?.response?.data?.detail || err.message || '获取图像记录失败'
    ElMessage.error(String(msg))
  } finally {
    imgLoading.value = false
  }
}

function onPredPageChange(page) {
  predPage.value = page
  loadPredictions()
}

function onImgPageChange(page) {
  imgPage.value = page
  loadImages()
}

onMounted(() => {
  loadPredictions()
  loadImages()
})
</script>

<style scoped>
.table-card {
  margin-bottom: 20px;
}
.card-title {
  font-weight: 600;
}
.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
