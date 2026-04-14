<template>
  <div class="task-list">
    <el-table :data="tasks" style="width: 100%">
      <el-table-column prop="title" label="任务标题" min-width="200">
        <template #default="{ row }">
          <el-link type="primary" @click="viewTask(row.id)">{{ row.title }}</el-link>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ getStatusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="100">
        <template #default="{ row }">
          <el-tag :type="getPriorityType(row.priority)" size="small">
            {{ getPriorityLabel(row.priority) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="assignee" label="负责人" width="120">
        <template #default="{ row }">
          {{ row.assignee ? `${row.assignee.first_name} ${row.assignee.last_name}` : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="due_date" label="截止日期" width="120">
        <template #default="{ row }">
          {{ formatDate(row.due_date) }}
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { Task } from '@/types'
import { formatDate } from '@/utils/formatters'

const props = defineProps<{
  tasks: Task[]
  projectId?: number
}>()

const emit = defineEmits<{
  refresh: []
}>()

const router = useRouter()

const viewTask = (id: number) => {
  router.push(`/tasks/${id}`)
}

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    todo: 'info',
    in_progress: 'warning',
    in_review: 'primary',
    done: 'success'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    todo: '待办',
    in_progress: '进行中',
    in_review: '审核中',
    done: '已完成'
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
</script>
