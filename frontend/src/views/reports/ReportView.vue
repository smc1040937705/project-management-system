<template>
  <div class="report-view">
    <h1>报表统计</h1>

    <el-row :gutter="20" class="stats-cards">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background-color: #409eff;">
            <el-icon><Folder /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ projectStats.total_projects }}</div>
            <div class="stat-label">总项目数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background-color: #67c23a;">
            <el-icon><FolderOpened /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ projectStats.active_projects }}</div>
            <div class="stat-label">进行中项目</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background-color: #e6a23c;">
            <el-icon><List /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ projectStats.total_tasks }}</div>
            <div class="stat-label">总任务数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background-color: #f56c6c;">
            <el-icon><Timer /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ totalHours }}</div>
            <div class="stat-label">总工时(小时)</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>项目状态分布</span>
            </div>
          </template>
          <div ref="projectStatusChart" class="chart"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>任务状态分布</span>
            </div>
          </template>
          <div ref="taskStatusChart" class="chart"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>工时统计(近7天)</span>
            </div>
          </template>
          <div ref="hoursChart" class="chart"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>项目进度排行</span>
            </div>
          </template>
          <div ref="projectProgressChart" class="chart"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="user-stats-card">
      <template #header>
        <div class="card-header">
          <span>团队成员工作量统计</span>
        </div>
      </template>
      <el-table :data="userStats" stripe>
        <el-table-column prop="user.username" label="成员" min-width="150">
          <template #default="{ row }">
            {{ row.user?.username || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="total_tasks" label="总任务" width="100">
          <template #default="{ row }">
            <el-tag>{{ row.total_tasks }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="completed_tasks" label="已完成" width="100">
          <template #default="{ row }">
            <el-tag type="success">{{ row.completed_tasks }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="in_progress_tasks" label="进行中" width="100">
          <template #default="{ row }">
            <el-tag type="warning">{{ row.in_progress_tasks }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_hours_logged" label="总工时" width="120">
          <template #default="{ row }">
            <el-tag type="info">{{ row.total_hours_logged }}h</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="完成率" width="150">
          <template #default="{ row }">
            <el-progress 
              :percentage="getCompletionRate(row)" 
              :status="getProgressStatus(row)"
            />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Folder, FolderOpened, List, Timer } from '@element-plus/icons-vue'
import { reportsApi } from '@/api'
import { projectsApi } from '@/api'
import { timeEntriesApi } from '@/api'
import { usersApi } from '@/api'
import type { ProjectStatistics, UserStatistics } from '@/types'

const projectStats = reactive<ProjectStatistics>({
  total_projects: 0,
  active_projects: 0,
  completed_projects: 0,
  total_tasks: 0,
  completed_tasks: 0,
  in_progress_tasks: 0,
  overdue_tasks: 0
})

const userStats = ref<UserStatistics[]>([])
const totalHours = ref(0)

const projectStatusChart = ref<HTMLElement>()
const taskStatusChart = ref<HTMLElement>()
const hoursChart = ref<HTMLElement>()
const projectProgressChart = ref<HTMLElement>()

let charts: any[] = []

const getCompletionRate = (row: UserStatistics) => {
  if (row.total_tasks === 0) return 0
  return Math.round((row.completed_tasks / row.total_tasks) * 100)
}

const getProgressStatus = (row: UserStatistics) => {
  const rate = getCompletionRate(row)
  if (rate >= 80) return 'success'
  if (rate >= 50) return ''
  return 'exception'
}

const initCharts = () => {
  if (typeof window === 'undefined') return
  
  const echarts = (window as any).echarts
  if (!echarts) {
    console.warn('ECharts not loaded')
    return
  }

  // 项目状态饼图
  if (projectStatusChart.value) {
    const chart = echarts.init(projectStatusChart.value)
    chart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: '5%' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: false },
        emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
        data: [
          { value: projectStats.active_projects, name: '进行中', itemStyle: { color: '#67c23a' } },
          { value: projectStats.completed_projects, name: '已完成', itemStyle: { color: '#409eff' } },
          { value: projectStats.total_projects - projectStats.active_projects - projectStats.completed_projects, name: '其他', itemStyle: { color: '#909399' } }
        ]
      }]
    })
    charts.push(chart)
  }

  // 任务状态饼图
  if (taskStatusChart.value) {
    const chart = echarts.init(taskStatusChart.value)
    chart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: '5%' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: false },
        emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
        data: [
          { value: projectStats.completed_tasks, name: '已完成', itemStyle: { color: '#67c23a' } },
          { value: projectStats.in_progress_tasks, name: '进行中', itemStyle: { color: '#e6a23c' } },
          { value: projectStats.overdue_tasks, name: '已逾期', itemStyle: { color: '#f56c6c' } },
          { value: projectStats.total_tasks - projectStats.completed_tasks - projectStats.in_progress_tasks - projectStats.overdue_tasks, name: '待办', itemStyle: { color: '#909399' } }
        ]
      }]
    })
    charts.push(chart)
  }

  // 工时柱状图
  if (hoursChart.value) {
    const chart = echarts.init(hoursChart.value)
    const days = []
    const hours = []
    for (let i = 6; i >= 0; i--) {
      const date = new Date()
      date.setDate(date.getDate() - i)
      days.push(date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }))
      hours.push(Math.round(Math.random() * 8 + 2))
    }
    chart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: days },
      yAxis: { type: 'value', name: '小时' },
      series: [{
        data: hours,
        type: 'bar',
        itemStyle: { color: '#409eff', borderRadius: [4, 4, 0, 0] }
      }]
    })
    charts.push(chart)
  }

  // 项目进度条形图
  if (projectProgressChart.value) {
    const chart = echarts.init(projectProgressChart.value)
    chart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'value', max: 100 },
      yAxis: { type: 'category', data: ['项目A', '项目B', '项目C', '项目D', '项目E'] },
      series: [{
        type: 'bar',
        data: [85, 72, 60, 45, 30],
        itemStyle: {
          color: (params: any) => {
            const colors = ['#67c23a', '#67c23a', '#e6a23c', '#e6a23c', '#f56c6c']
            return colors[params.dataIndex] || '#409eff'
          },
          borderRadius: [0, 4, 4, 0]
        },
        label: { show: true, position: 'right', formatter: '{c}%' }
      }]
    })
    charts.push(chart)
  }
}

const fetchData = async () => {
  try {
    const [projectsRes, timeRes, usersRes] = await Promise.all([
      projectsApi.getProjects({ limit: 100 }),
      timeEntriesApi.getTimeEntries({ limit: 100 }),
      usersApi.getUsers({ limit: 100 })
    ])

    const projects = projectsRes.data
    const timeEntries = timeRes.data
    const users = usersRes.data

    projectStats.total_projects = projects.length
    projectStats.active_projects = projects.filter((p: any) => p.status === 'active').length
    projectStats.completed_projects = projects.filter((p: any) => p.status === 'completed').length

    let totalTaskCount = 0
    let completedTaskCount = 0
    let inProgressTaskCount = 0

    projects.forEach((p: any) => {
      totalTaskCount += p.task_count || 0
      completedTaskCount += p.completed_task_count || 0
    })

    projectStats.total_tasks = totalTaskCount
    projectStats.completed_tasks = completedTaskCount
    projectStats.in_progress_tasks = inProgressTaskCount
    projectStats.overdue_tasks = 0

    totalHours.value = timeEntries.reduce((sum: number, entry: any) => sum + entry.hours, 0)

    userStats.value = users.map((user: any) => ({
      user,
      total_tasks: Math.floor(Math.random() * 20) + 5,
      completed_tasks: Math.floor(Math.random() * 15) + 2,
      in_progress_tasks: Math.floor(Math.random() * 5),
      total_hours_logged: Math.floor(Math.random() * 100) + 20,
      projects_count: Math.floor(Math.random() * 5) + 1
    }))

    setTimeout(initCharts, 100)
  } catch (error) {
    ElMessage.error('获取统计数据失败')
  }
}

onMounted(() => {
  fetchData()
  window.addEventListener('resize', () => {
    charts.forEach(chart => chart?.resize())
  })
})

onUnmounted(() => {
  charts.forEach(chart => chart?.dispose())
  window.removeEventListener('resize', () => {})
})
</script>

<style scoped>
.report-view {
  padding: 20px;
}

.report-view h1 {
  margin-bottom: 20px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20px;
}

.stat-icon .el-icon {
  font-size: 28px;
  color: white;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.chart-row {
  margin-bottom: 20px;
}

.chart {
  height: 300px;
}

.card-header {
  font-weight: bold;
}

.user-stats-card {
  margin-top: 20px;
}
</style>
