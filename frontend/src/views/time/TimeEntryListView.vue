<template>
  <div class="time-entry-list">
    <div class="header">
      <h1>工时记录</h1>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>记录工时
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
        <el-form-item label="任务">
          <el-select v-model="filterForm.task_id" placeholder="选择任务" clearable style="width: 180px">
            <el-option
              v-for="task in filteredTasks"
              :key="task.id"
              :label="task.title"
              :value="task.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="filterForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-row :gutter="20" class="stats-row">
        <el-col :span="8">
          <el-statistic title="总工时" :value="totalHours" suffix="小时" />
        </el-col>
        <el-col :span="8">
          <el-statistic title="记录条数" :value="totalEntries" />
        </el-col>
        <el-col :span="8">
          <el-statistic title="今日工时" :value="todayHours" suffix="小时" />
        </el-col>
      </el-row>

      <el-table :data="timeEntries" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="task.title" label="任务" min-width="150">
          <template #default="{ row }">
            {{ row.task?.title || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="task.project.name" label="项目" width="150">
          <template #default="{ row }">
            {{ row.task?.project?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="description" label="工作内容" min-width="200">
          <template #default="{ row }">
            {{ row.description || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="hours" label="工时" width="80">
          <template #default="{ row }">
            <el-tag type="success">{{ row.hours }}h</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="date" label="日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.date) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="记录时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
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

    <TimeEntryFormDialog
      v-model:visible="dialogVisible"
      :timeEntry="currentTimeEntry"
      :projects="projects"
      :tasks="tasks"
      @success="handleSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { timeEntriesApi } from '@/api'
import { projectsApi } from '@/api'
import { tasksApi } from '@/api'
import type { TimeEntry, Project, Task } from '@/types'
import TimeEntryFormDialog from '@/components/time/TimeEntryFormDialog.vue'

const loading = ref(false)
const timeEntries = ref<TimeEntry[]>([])
const projects = ref<Project[]>([])
const tasks = ref<Task[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const filterForm = reactive({
  project_id: undefined as number | undefined,
  task_id: undefined as number | undefined,
  dateRange: [] as string[]
})

const dialogVisible = ref(false)
const currentTimeEntry = ref<TimeEntry | null>(null)

const filteredTasks = computed(() => {
  if (!filterForm.project_id) return tasks.value
  return tasks.value.filter(t => t.project_id === filterForm.project_id)
})

const totalHours = computed(() => {
  return timeEntries.value.reduce((sum, entry) => sum + entry.hours, 0)
})

const totalEntries = computed(() => timeEntries.value.length)

const todayHours = computed(() => {
  const today = new Date().toISOString().split('T')[0]
  return timeEntries.value
    .filter(entry => entry.date.split('T')[0] === today)
    .reduce((sum, entry) => sum + entry.hours, 0)
})

const formatDate = (date?: string) => {
  if (!date) return '-'
  return date.split('T')[0]
}

const formatDateTime = (date?: string) => {
  if (!date) return '-'
  return date.replace('T', ' ').substring(0, 16)
}

const fetchTimeEntries = async () => {
  loading.value = true
  try {
    const params: any = {
      skip: (page.value - 1) * pageSize.value,
      limit: pageSize.value
    }
    if (filterForm.task_id) params.task_id = filterForm.task_id
    if (filterForm.dateRange && filterForm.dateRange.length === 2) {
      params.start_date = filterForm.dateRange[0]
      params.end_date = filterForm.dateRange[1]
    }

    const response = await timeEntriesApi.getTimeEntries(params)
    timeEntries.value = response.data
    total.value = response.data.length
  } catch (error) {
    ElMessage.error('获取工时记录失败')
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

const fetchTasks = async () => {
  try {
    const response = await tasksApi.getTasks({ limit: 100 })
    tasks.value = response.data
  } catch (error) {
    console.error('获取任务列表失败', error)
  }
}

const handleSearch = () => {
  page.value = 1
  fetchTimeEntries()
}

const handleReset = () => {
  filterForm.project_id = undefined
  filterForm.task_id = undefined
  filterForm.dateRange = []
  handleSearch()
}

const handlePageChange = (val: number) => {
  page.value = val
  fetchTimeEntries()
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  page.value = 1
  fetchTimeEntries()
}

const handleCreate = () => {
  currentTimeEntry.value = null
  dialogVisible.value = true
}

const handleEdit = (entry: TimeEntry) => {
  currentTimeEntry.value = entry
  dialogVisible.value = true
}

const handleDelete = async (entry: TimeEntry) => {
  try {
    await ElMessageBox.confirm('确定要删除该工时记录吗？', '提示', {
      type: 'warning'
    })
    await timeEntriesApi.deleteTimeEntry(entry.id)
    ElMessage.success('删除成功')
    fetchTimeEntries()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleSuccess = () => {
  dialogVisible.value = false
  fetchTimeEntries()
}

onMounted(() => {
  fetchTimeEntries()
  fetchProjects()
  fetchTasks()
})
</script>

<style scoped>
.time-entry-list {
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

.stats-row {
  margin-bottom: 20px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
