<template>
  <div class="monitor">
    <el-card shadow="never" class="upload-card">
      <template #header>
        <span class="card-title">熔池图像上传</span>
      </template>
      <el-upload
        drag
        :show-file-list="false"
        accept=".png,.jpg,.jpeg,.bmp,.tif,.tiff"
        :before-upload="beforeUpload"
        :http-request="uploadImage"
        :disabled="loading"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">将熔池图像拖到此处，或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">仅支持常见图片格式（PNG/JPG/BMP/TIFF），单张灰度熔池图像</div>
        </template>
      </el-upload>
    </el-card>

    <div v-if="loading" v-loading="loading" class="loading-placeholder"></div>

    <el-row v-if="result" :gutter="20" class="result-row">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span class="card-title">原始图像</span></template>
          <div class="img-box">
            <img v-if="originalUrl" :src="originalUrl" class="preview-img" alt="原图" />
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span class="card-title">熔池 ROI 图像</span></template>
          <div class="img-box">
            <img v-if="roiUrl" :src="roiUrl" class="preview-img" alt="ROI" />
            <el-empty v-else description="无 ROI 结果" :image-size="80" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card v-if="result" shadow="never" class="result-card">
      <template #header><span class="card-title">分类结果</span></template>

      <div class="label-row">
        <el-tag size="large" :type="labelTagType" effect="dark">
          {{ result.label_name }}
        </el-tag>
        <span class="confidence-text">
          置信度 {{ (result.confidence * 100).toFixed(2) }}%
        </span>
      </div>

      <el-progress
        :percentage="Math.round(result.confidence * 100)"
        :stroke-width="16"
        :color="labelColor"
        class="confidence-bar"
      />

      <el-divider content-position="left">三分类概率</el-divider>
      <div v-for="(p, i) in result.probs" :key="i" class="prob-row">
        <span class="prob-label">{{ labelNames[i] }}</span>
        <el-progress
          :percentage="Math.round(p * 100)"
          :stroke-width="12"
          :color="probColors[i]"
          class="prob-bar"
        />
        <span class="prob-value">{{ (p * 100).toFixed(2) }}%</span>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { classifyImage } from '../api'

const labelNames = ['致密/良好', '气孔', '裂纹/未熔合']
const probColors = ['#67c23a', '#e6a23c', '#f56c6c']
const labelColorMap = { 0: '#67c23a', 1: '#e6a23c', 2: '#f56c6c' }
const tagTypeMap = { 0: 'success', 1: 'warning', 2: 'danger' }

const loading = ref(false)
const result = ref(null)
const originalUrl = ref('')
const roiUrl = ref('')

const labelColor = ref('#67c23a')
const labelTagType = ref('success')

function beforeUpload(file) {
  const isImage = /image\/(png|jpe?g|bmp|tiff?)/.test(file.type) || /\.(png|jpe?g|bmp|tiff?)$/i.test(file.name)
  if (!isImage) {
    ElMessage.error('请上传图片格式文件（PNG/JPG/BMP/TIFF）')
    return false
  }
  return true
}

async function uploadImage(options) {
  const file = options.file
  loading.value = true
  try {
    const res = await classifyImage(file)
    const data = res.data
    result.value = data
    labelColor.value = labelColorMap[data.label] || '#909399'
    labelTagType.value = tagTypeMap[data.label] || 'info'

    originalUrl.value = URL.createObjectURL(file)
    roiUrl.value = data.roi_base64 ? `data:image/png;base64,${data.roi_base64}` : ''
  } catch (err) {
    const msg = err?.response?.data?.detail || err.message || '分类请求失败'
    ElMessage.error(String(msg))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.upload-card {
  margin-bottom: 20px;
}
.card-title {
  font-weight: 600;
}
.loading-placeholder {
  height: 120px;
}
.result-row {
  margin-bottom: 20px;
}
.img-box {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 220px;
  background: #fafafa;
  border-radius: 4px;
}
.preview-img {
  max-width: 100%;
  max-height: 320px;
  image-rendering: pixelated;
}
.result-card {
  margin-top: 20px;
}
.label-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}
.confidence-text {
  color: #606266;
}
.confidence-bar {
  margin-bottom: 8px;
}
.prob-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.prob-label {
  width: 90px;
  color: #606266;
  flex-shrink: 0;
}
.prob-bar {
  flex: 1;
}
.prob-value {
  width: 70px;
  text-align: right;
  color: #303133;
  flex-shrink: 0;
}
</style>
