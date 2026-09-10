import axios from 'axios'

const request = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// 1. 健康检查
export function getHealth() {
  return request.get('/health')
}

// 2. 熔池图像分类（multipart，字段名 file）
export function classifyImage(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/classify', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// 3. 工艺参数质量预测
export function predict(params) {
  return request.post('/predict', params)
}

// 4. 异常检测
export function detectAnomaly(jobId) {
  return request.post('/anomaly', { job_id: jobId })
}

// 5. 预测历史
export function getPredictionHistory(limit = 20, offset = 0) {
  return request.get('/history/predictions', { params: { limit, offset } })
}

// 6. 图像记录
export function getImageHistory(limit = 20, offset = 0) {
  return request.get('/history/images', { params: { limit, offset } })
}

// 7. 传感器 job 列表
export function getJobs() {
  return request.get('/sensors/jobs')
}

export default request
