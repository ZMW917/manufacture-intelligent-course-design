import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/monitor' },
  { path: '/monitor', name: 'Monitor', component: () => import('../views/Monitor.vue') },
  { path: '/predict', name: 'Predict', component: () => import('../views/Predict.vue') },
  { path: '/anomaly', name: 'Anomaly', component: () => import('../views/Anomaly.vue') },
  { path: '/history', name: 'History', component: () => import('../views/History.vue') },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
