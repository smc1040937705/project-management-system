<template>
  <div class="project-list">
    <div class="page-header">
      <h1>项目列表</h1>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>新建项目
      </el-button>
    </div>
    
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部状态" clearable>
            <el-option label="规划中" value="planning" />
            <el-option label="进行中" value="active" />
            <el-option label="暂停" value="on_hold" />
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input v-model="filterForm.search" placeholder="项目名称/描述" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilter">筛选</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-table v-loading="loading" :data="projects" style="width: 100%">
      <el-table-column prop="name" label="项目名称" min-width="200">
        <template #default="{ row }">
          <el-link type="primary" @click="viewProject(row.id)">{{ row.name }}</el-link>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="owner" label="负责人" width="150">
        <template #default="{ row }">
          {{ row.owner.first_name }} {{ row.owner.last_name }}
        </template>
      </el-table-column>
      <el-table-column prop="task_count" label="任务数" width="100">
        <template #default="{ row }">
          {{ row.completed_task_count }}/{{ row.task_count }}
        </template>
      </el-table-column>
      <el-table-column prop="start_date" label="开始日期" width="120">
        <template #default="{ row }">
          {{ formatDate(row.start_date) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="viewProject(row.id)">查看</el-button>
          <el-button link type="primary" @click="editProject(row)">编辑</el-button>
          <el-button link type="danger" @click="deleteProject(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <el-dialog v-model="showCreateDialog" title="新建项目" width="600px">
      <ProjectForm ref="createFormRef" @submit="handleCreate" @cancel="showCreateDialog = false" />
    </el-dialog>
    
    <el-dialog v-model="showEditDialog" title="编辑项目" width="600px">
      <ProjectForm 
        v-if="editingProject" 
        ref="editFormRef" 
        :project="editingProject"
        @submit="handleEdit" 
        @cancel="showEditDialog = false" 
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useProjectsStore } from '@/stores/projects'
import ProjectForm from '@/components/projects/ProjectForm.vue'
import type { Project } from '@/types'
import { formatDate } from '@/utils/formatters'

const router = useRouter()
const projectsStore = useProjectsStore()
const projects = ref<Project[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const editingProject = ref<Project | null>(null)

const filterForm = ref({
  status: '',
  search: ''
})

const fetchProjects = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (filterForm.value.status) params.status = filterForm.value.status
    if (filterForm.value.search) params.search = filterForm.value.search
    
    await projectsStore.fetchProjects(params)
    projects.value = projectsStore.projects
  } catch (error) {
    ElMessage.error('获取项目列表失败')
  } finally {
    loading.value = false
  }
}

const handleFilter = () => {
  fetchProjects()
}

const resetFilter = () => {
  filterForm.value = { status: '', search: '' }
  fetchProjects()
}

const viewProject = (id: number) => {
  router.push(`/projects/${id}`)
}

const editProject = (project: Project) => {
  editingProject.value = project
  showEditDialog.value = true
}

const deleteProject = async (project: Project) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目 "${project.name}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await projectsStore.deleteProject(project.id)
    ElMessage.success('删除成功')
    fetchProjects()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleCreate = async (data: any) => {
  try {
    await projectsStore.createProject(data)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    fetchProjects()
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

const handleEdit = async (data: any) => {
  if (!editingProject.value) return
  try {
    await projectsStore.updateProject(editingProject.value.id, data)
    ElMessage.success('更新成功')
    showEditDialog.value = false
    fetchProjects()
  } catch (error) {
    ElMessage.error('更新失败')
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

onMounted(fetchProjects)
</script>

<style scoped>
.project-list {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filter-card {
  margin-bottom: 20px;
}
</style>
