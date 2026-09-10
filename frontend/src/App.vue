<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="logo">LPBF 监测系统</div>
      <el-menu
        :default-active="activeMenu"
        router
        class="menu"
        background-color="#001529"
        text-color="#a6adb4"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/monitor">
          <el-icon><Camera /></el-icon>
          <span>熔池监测</span>
        </el-menu-item>
        <el-menu-item index="/predict">
          <el-icon><TrendCharts /></el-icon>
          <span>质量预测</span>
        </el-menu-item>
        <el-menu-item index="/anomaly">
          <el-icon><Warning /></el-icon>
          <span>异常预警</span>
        </el-menu-item>
        <el-menu-item index="/history">
          <el-icon><Clock /></el-icon>
          <span>历史记录</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        LPBF 熔池在线监测与成形质量智能预测系统
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style>
html,
body,
#app {
  height: 100%;
  margin: 0;
  padding: 0;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif;
}
</style>

<style scoped>
.layout {
  height: 100%;
}
.aside {
  background: #001529;
}
.logo {
  height: 60px;
  color: #ffffff;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.menu {
  border-right: none;
}
.header {
  background: #ffffff;
  border-bottom: 1px solid #e5e6eb;
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: #1d2129;
}
.main {
  background: #f2f3f5;
  padding: 20px;
}
</style>
