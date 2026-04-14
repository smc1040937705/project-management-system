<template>
  <div class="task-list">
    <div class="header">
      <h1>任务管理</h1>
      <el-button type="primary" @click="handleCreate" v-if="canCreate">
        <el-icon><Plus /></el-icon>新建任务
      </el-button>
    </div>

    <el-card>
      <el-form :model="filterForm" inline class="filter-form">
        <el-form-item label="项目">
          <el-select v-model="filterForm.project_id" placeholder="选择项目" clearable style="width: 180px">
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="选择状态" clearable style="width: 120px">
            <el-option label="待办" value="todo" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="审核中" value="in_review" />
            <el-option label="已完成" value="done" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="filterForm.priority" placeholder="选择优先级" clearable style="width: 120px">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人">
          <el-select v-model="filterForm.assignee_id" placeholder="选择负责人" clearable style="width: 150px">
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="tasks" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="任务标题" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" @click="handleView(row)">{{ row.title }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="project.name" label="所属项目" width="150">
          <template #default="{ row }">
            {{ row.project?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="90">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)" size="small">
              {{ getPriorityLabel(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="assignee" label="负责人" width="120">
          <template #default="{ row }">
            {{ row.assignee?.username || '未分配' }}
          </template>
        </el-table-column>
        <el-table-column prop="due_date" label="截止日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.due_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="actual_hours" label="工时" width="80">
          <template #default="{ row }">
            {{ row.actual_hours || 0 }}h
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleView(row)">查看</el-button>
            <el-button link type="primary" @click="handleEdit(row)" v-if="canEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)" v-if="canDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <TaskFormDialog
      v-model:visible="dialogVisible"
      :task="currentTask"
      :projects="projects"
      :users="users"
      @success="handleSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { tasksApi } from '@/api'
import { projectsApi } from '@/api'
import { usersApi } from '@/api'
import type { Task, Project, User } from '@/types'
import TaskFormDialog from '@/components/tasks/TaskFormDialog.vue'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const tasks = ref<Task[]>([])
const projects = ref<Project[]>([])
const users = ref<User[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const filterForm = reactive({
  project_id: undefined as number | undefined,
  status: '',
  priority: '',
  assignee_id: undefined as number | undefined
})

const dialogVisible = ref(false)
const currentTask = ref<Task | null>(null)

const canCreate = computed(() => {
  // 所有登录用户都可以创建任务
  return !!authStore.user
})

const canEdit = (task: Task) => {
  return task.assignee_id === authStore.user?.id || 
         ['admin', 'project_manager'].includes(authStore.user?.role || '')
}

const canDelete = (task: Task) => {
  return ['admin', 'project_manager'].includes(authStore.user?.role || '')
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    todo: 'info',
    in_progress: 'warning',
    in_review: 'primary',
    done: 'success'
  }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    todo: '待办',
    in_progress: '进行中',
    in_review: '审核中',
    done: '已完成'
  }
  return map[status] || status
}

const getPriorityType = (priority: string) => {
  const map: Record<string, string> = {
    low: 'info',
    medium: 'success',
    high: 'warning',
    critical: 'danger'
  }
  return map[priority] || 'info'
}

const getPriorityLabel = (priority: string) => {
  const map: Record<string, string> = {
    low: '低',
    medium: '中',
    high: '高',
    critical: '紧急'
  }
  return map[priority] || priority
}

const formatDate = (date?: string) => {
  if (!date) return '-'
  return date.split('T')[0]
}

const fetchTasks = async () => {
  loading.value = true
  try {
    const params: any = {
      skip: (page.value - 1) * pageSize.value,
      limit: pageSize.value
    }
    if (filterForm.project_id) params.project_id = filterForm.project_id
    if (filterForm.status) params.status = filterForm.status
    if (filterForm.priority) params.priority = filterForm.priority
    if (filterForm.assignee_id) params.assignee_id = filterForm.assignee_id

    const response = await tasksApi.getTasks(params)
    tasks.value = response.data
    total.value = response.data.length
  } catch (error) {
    ElMessage.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}

const fetchProjects = async () => {
  try {
    const response = await projectsApi.getProjects({ limit: 100 })
    projects.value = response.data
  } catch (error) {
    console.error('获取项目列表失败', error)
  }
}

const fetchUsers = async () => {
  try {
    const response = await usersApi.getUsers({ limit: 100 })
    users.value = response.data
  } catch (error) {
    console.error('获取用户列表失败', error)
  }
}

const handleSearch = () => {
  page.value = 1
  fetchTasks()
}

const handleReset = () => {
  filterForm.project_id = undefined
  filterForm.status = ''
  filterForm.priority = ''
  filterForm.assignee_id = undefined
  handleSearch()
}

const handlePageChange = (val: number) => {
  page.value = val
  fetchTasks()
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  page.value = 1
  fetchTasks()
}

const handleCreate = () => {
  currentTask.value = null
  dialogVisible.value = true
}

const handleView = (task: Task) => {
  router.push(`/tasks/${task.id}`)
}

const handleEdit = (task: Task) => {
  currentTask.value = task
  dialogVisible.value = true
}

const handleDelete = async (task: Task) => {
  try {
    await ElMessageBox.confirm('确定要删除该任务吗？', '提示', {
      type: 'warning'
    })
    await tasksApi.deleteTask(task.id)
    ElMessage.success('删除成功')
    fetchTasks()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleSuccess = () => {
  dialogVisible.value = false
  fetchTasks()
}

onMounted(() => {
  fetchTasks()
  fetchProjects()
  fetchUsers()
})
</script>

<style scoped>
.task-list {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h1 {
  margin: 0;
}

.filter-form {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
