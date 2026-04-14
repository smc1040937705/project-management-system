<template>
  <el-dialog
    title="上传文档"
    v-model="dialogVisible"
    width="500px"
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      class="upload-form"
    >
      <el-form-item label="所属项目" prop="project_id">
        <el-select v-model="form.project_id" placeholder="选择项目" style="width: 100%">
          <el-option
            v-for="project in projects"
            :key="project.id"
            :label="project.name"
            :value="project.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="文档名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入文档名称" />
      </el-form-item>

      <el-form-item label="选择文件" prop="file">
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          :limit="1"
          drag
          style="width: 100%"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            拖拽文件到此处或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持各类文档格式，单个文件不超过 50MB
            </div>
          </template>
        </el-upload>
      </el-form-item>

      <el-form-item label="备注" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入备注信息（可选）"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="uploading">上传</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules, UploadFile, UploadInstance } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { documentsApi } from '@/api'
import type { Project } from '@/types'

const props = defineProps<{
  visible: boolean
  projects: Project[]
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

const formRef = ref<FormInstance>()
const uploadRef = ref<UploadInstance>()
const uploading = ref(false)
const selectedFile = ref<File | null>(null)

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const form = reactive({
  project_id: undefined as number | undefined,
  name: '',
  description: ''
})

const rules: FormRules = {
  project_id: [
    { required: true, message: '请选择所属项目', trigger: 'change' }
  ],
  name: [
    { required: true, message: '请输入文档名称', trigger: 'blur' },
    { min: 1, max: 200, message: '长度在 1 到 200 个字符', trigger: 'blur' }
  ]
}

const handleFileChange = (uploadFile: UploadFile) => {
  selectedFile.value = uploadFile.raw || null
  if (uploadFile.name && !form.name) {
    form.name = uploadFile.name.replace(/\.[^/.]+$/, '')
  }
}

const handleFileRemove = () => {
  selectedFile.value = null
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    if (!selectedFile.value) {
      ElMessage.warning('请选择要上传的文件')
      return
    }

    uploading.value = true
    try {
      const formData = new FormData()
      formData.append('file', selectedFile.value)
      formData.append('project_id', form.project_id!.toString())
      formData.append('name', form.name)
      if (form.description) {
        formData.append('description', form.description)
      }

      await documentsApi.uploadDocument(form.project_id!, selectedFile.value, form.name, form.description)
      ElMessage.success('上传成功')
      
      form.project_id = undefined
      form.name = ''
      form.description = ''
      selectedFile.value = null
      uploadRef.value?.clearFiles()
      
      emit('success')
    } catch (error) {
      ElMessage.error('上传失败')
    } finally {
      uploading.value = false
    }
  })
}
</script>

<style scoped>
.upload-form {
  padding: 10px 0;
}
</style>
