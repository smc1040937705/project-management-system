<template>
  <div v-if="project" class="project-detail">
    <el-page-header @back="$router.push('/projects')" :title="project.name" />
    
    <el-card class="project-info">
      <template #header>
        <div class="card-header">
          <span>项目信息</span>
          <el-button type="primary" @click="$router.push(`/projects/${project.id}/edit`)">
            编辑
          </el-button>
        </div>
      </template>
      
      <el-descriptions :column="2">
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(project.status)">
            {{ getStatusLabel(project.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="负责人">
          {{ project.owner.first_name }} {{ project.owner.last_name }}
        </el-descriptions-item>
        <el-descriptions-item label="开始日期">
          {{ formatDate(project.start_date) }}
        </el-descriptions-item>
        <el-descriptions-item label="结束日期">
          {{ formatDate(project.end_date) }}
        </el-descriptions-item>
        <el-descriptions-item label="预算">
          {{ project.budget ? formatCurrency(project.budget) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="任务进度">
          {{ project.completed_task_count }}/{{ project.task_count }}
        </el-descriptions-item>
      </el-descriptions>
      
      <div class="project-description">
        <h4>项目描述</h4>
        <p>{{ project.description || '暂无描述' }}</p>
      </div>
    </el-card>
    
    <el-row :gutter="20" class="project-content">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>任务列表</span>
              <el-button type="primary" size="small" @click="showTaskDialog = true">
                新建任务
              </el-button>
            </div>
          </template>
          <TaskList :tasks="tasks" :project-id="project.id" @refresh="fetchTasks" />
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>团队成员</span>
          </template>
          <MemberList :members="project.members" :project-id="project.id" @refresh="fetchProject" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'
import TaskList from '@/components/tasks/TaskList.vue'
import MemberList from '@/components/projects/MemberList.vue'
import type { Project, Task } from '@/types'
import { formatDate, formatCurrency } from '@/utils/formatters'

const route = useRoute()
const projectsStore = useProjectsStore()
const tasksStore = useTasksStore()
const project = ref<Project | null>(null)
const tasks = ref<Task[]>([])
const showTaskDialog = ref(false)

const fetchProject = async () => {
  try {
    const id = parseInt(route.params.id as string)
    project.value = await projectsStore.fetchProject(id)
  } catch (error) {
    ElMessage.error('获取项目信息失败')
  }
}

const fetchTasks = async () => {
  try {
    const id = parseInt(route.params.id as string)
    await tasksStore.fetchTasks({ project_id: id })
    tasks.value = tasksStore.tasks
  } catch (error) {
    ElMessage.error('获取任务列表失败')
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

onMounted(() => {
  fetchProject()
  fetchTasks()
})
</script>

<style scoped>
.project-detail {
  padding: 20px;
}

.project-info {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.project-description {
  margin-top: 20px;
}

.project-description h4 {
  margin-bottom: 10px;
  color: #606266;
}

.project-content {
  margin-top: 20px;
}
</style>
