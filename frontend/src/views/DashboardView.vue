<template>
  <div class="dashboard">
    <h1>仪表盘</h1>
    
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #409EFF;">
            <el-icon size="32"><FolderOpened /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.total_projects }}</div>
            <div class="stat-label">总项目</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #67C23A;">
            <el-icon size="32"><List /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.total_tasks }}</div>
            <div class="stat-label">总任务</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #E6A23C;">
            <el-icon size="32"><Timer /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.in_progress_tasks }}</div>
            <div class="stat-label">进行中</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #F56C6C;">
            <el-icon size="32"><Warning /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.overdue_tasks }}</div>
            <div class="stat-label">已逾期</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="content-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>最近项目</span>
            <el-button text @click="$router.push('/projects')">查看全部</el-button>
          </template>
          <el-table :data="recentProjects" style="width: 100%">
            <el-table-column prop="name" label="项目名称" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">
                  {{ getStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="task_count" label="任务数" width="80" />
          </el-table>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>我的任务</span>
            <el-button text @click="$router.push('/tasks')">查看全部</el-button>
          </template>
          <el-table :data="myTasks" style="width: 100%">
            <el-table-column prop="title" label="任务标题" />
            <el-table-column prop="priority" label="优先级" width="100">
              <template #default="{ row }">
                <el-tag :type="getPriorityType(row.priority)" size="small">
                  {{ getPriorityLabel(row.priority) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getTaskStatusType(row.status)" size="small">
                  {{ getTaskStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { reportsApi, projectsApi, tasksApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import type { ProjectStatistics, Project, Task } from '@/types'

const authStore = useAuthStore()
const statistics = ref<ProjectStatistics>({
  total_projects: 0,
  active_projects: 0,
  completed_projects: 0,
  total_tasks: 0,
  completed_tasks: 0,
  in_progress_tasks: 0,
  overdue_tasks: 0
})
const recentProjects = ref<Project[]>([])
const myTasks = ref<Task[]>([])

const fetchData = async () => {
  try {
    if (authStore.isProjectManager) {
      const statsResponse = await reportsApi.getProjectStatistics()
      statistics.value = statsResponse.data
    }
    
    const projectsResponse = await projectsApi.getProjects({ limit: 5 })
    recentProjects.value = projectsResponse.data
    
    const tasksResponse = await tasksApi.getTasks({ 
      assignee_id: authStore.user?.id,
      limit: 5 
    })
    myTasks.value = tasksResponse.data
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  }
}

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    planning: 'info',
    active: 'success',
    on_hold: 'warning',
    completed: 'success',
    cancelled: 'danger'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    planning: '规划中',
    active: '进行中',
    on_hold: '暂停',
    completed: '已完成',
    cancelled: '已取消'
  }
  return labels[status] || status
}

const getPriorityType = (priority: string) => {
  const types: Record<string, string> = {
    low: 'info',
    medium: 'warning',
    high: 'danger',
    critical: 'danger'
  }
  return types[priority] || 'info'
}

const getPriorityLabel = (priority: string) => {
  const labels: Record<string, string> = {
    low: '低',
    medium: '中',
    high: '高',
    critical: '紧急'
  }
  return labels[priority] || priority
}

const getTaskStatusType = (status: string) => {
  const types: Record<string, string> = {
    todo: 'info',
    in_progress: 'warning',
    in_review: 'primary',
    done: 'success'
  }
  return types[status] || 'info'
}

const getTaskStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    todo: '待办',
    in_progress: '进行中',
    in_review: '审核中',
    done: '已完成'
  }
  return labels[status] || status
}

onMounted(fetchData)
</script>

<style scoped>
.dashboard h1 {
  margin-bottom: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 10px;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-right: 16px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.content-row {
  margin-top: 20px;
}

.content-row .el-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
