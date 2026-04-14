<template>
  <div class="document-list">
    <div class="header">
      <h1>文档管理</h1>
      <el-button type="primary" @click="handleUpload">
        <el-icon><Upload /></el-icon>上传文档
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
        <el-form-item label="文件名">
          <el-input v-model="filterForm.search" placeholder="搜索文件名" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="documents" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="文件名" min-width="200">
          <template #default="{ row }">
            <div class="file-name">
              <el-icon class="file-icon"><Document /></el-icon>
              <el-link type="primary" @click="handleDownload(row)">{{ row.name }}</el-link>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="project.name" label="所属项目" width="150">
          <template #default="{ row }">
            {{ row.project?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="大小" width="100">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="mime_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ getFileType(row.mime_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="uploader.username" label="上传者" width="120">
          <template #default="{ row }">
            {{ row.uploader?.username || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="80">
          <template #default="{ row }">
            <el-tag type="info" size="small">v{{ row.version }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleDownload(row)">下载</el-button>
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

    <DocumentUploadDialog
      v-model:visible="dialogVisible"
      :projects="projects"
      @success="handleSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Document } from '@element-plus/icons-vue'
import { documentsApi } from '@/api'
import { projectsApi } from '@/api'
import type { Document as DocType, Project } from '@/types'
import DocumentUploadDialog from '@/components/documents/DocumentUploadDialog.vue'

const loading = ref(false)
const documents = ref<DocType[]>([])
const projects = ref<Project[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const filterForm = reactive({
  project_id: undefined as number | undefined,
  search: ''
})

const dialogVisible = ref(false)

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getFileType = (mimeType: string) => {
  const typeMap: Record<string, string> = {
    'application/pdf': 'PDF',
    'application/msword': 'Word',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word',
    'application/vnd.ms-excel': 'Excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'Excel',
    'application/vnd.ms-powerpoint': 'PPT',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'PPT',
    'image/jpeg': '图片',
    'image/png': '图片',
    'image/gif': '图片',
    'text/plain': '文本',
    'application/zip': '压缩包',
    'application/x-rar-compressed': '压缩包'
  }
  return typeMap[mimeType] || '文件'
}

const formatDateTime = (date?: string) => {
  if (!date) return '-'
  return date.replace('T', ' ').substring(0, 16)
}

const fetchDocuments = async () => {
  loading.value = true
  try {
    const params: any = {
      skip: (page.value - 1) * pageSize.value,
      limit: pageSize.value
    }
    if (filterForm.project_id) params.project_id = filterForm.project_id
    if (filterForm.search) params.search = filterForm.search

    const response = await documentsApi.getDocuments(params)
    documents.value = response.data
    total.value = response.data.length
  } catch (error) {
    ElMessage.error('获取文档列表失败')
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

const handleSearch = () => {
  page.value = 1
  fetchDocuments()
}

const handleReset = () => {
  filterForm.project_id = undefined
  filterForm.search = ''
  handleSearch()
}

const handlePageChange = (val: number) => {
  page.value = val
  fetchDocuments()
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  page.value = 1
  fetchDocuments()
}

const handleUpload = () => {
  dialogVisible.value = true
}

const handleDownload = (doc: DocType) => {
  documentsApi.downloadDocument(doc.id)
}

const handleDelete = async (doc: DocType) => {
  try {
    await ElMessageBox.confirm('确定要删除该文档吗？', '提示', {
      type: 'warning'
    })
    await documentsApi.deleteDocument(doc.id)
    ElMessage.success('删除成功')
    fetchDocuments()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleSuccess = () => {
  dialogVisible.value = false
  fetchDocuments()
}

onMounted(() => {
  fetchDocuments()
  fetchProjects()
})
</script>

<style scoped>
.document-list {
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

.file-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-icon {
  font-size: 18px;
  color: #409eff;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
