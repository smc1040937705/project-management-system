<template>
  <el-dialog
    :title="isEdit ? '编辑任务' : '新建任务'"
    v-model="dialogVisible"
    width="600px"
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      class="task-form"
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

      <el-form-item label="任务标题" prop="title">
        <el-input v-model="form.title" placeholder="请输入任务标题" />
      </el-form-item>

      <el-form-item label="任务描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入任务描述"
        />
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="状态" prop="status">
            <el-select v-model="form.status" placeholder="选择状态" style="width: 100%">
              <el-option label="待办" value="todo" />
              <el-option label="进行中" value="in_progress" />
              <el-option label="审核中" value="in_review" />
              <el-option label="已完成" value="done" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="优先级" prop="priority">
            <el-select v-model="form.priority" placeholder="选择优先级" style="width: 100%">
              <el-option label="低" value="low" />
              <el-option label="中" value="medium" />
              <el-option label="高" value="high" />
              <el-option label="紧急" value="critical" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="负责人" prop="assignee_id">
            <el-select v-model="form.assignee_id" placeholder="选择负责人" clearable style="width: 100%">
              <el-option
                v-for="user in users"
                :key="user.id"
                :label="user.username"
                :value="user.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="截止日期" prop="due_date">
            <el-date-picker
              v-model="form.due_date"
              type="date"
              placeholder="选择截止日期"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="预计工时" prop="estimated_hours">
            <el-input-number
              v-model="form.estimated_hours"
              :min="0"
              :precision="1"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { tasksApi } from '@/api'
import type { Task, Project, User } from '@/types'

const props = defineProps<{
  visible: boolean
  task: Task | null
  projects: Project[]
  users: User[]
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

const formRef = ref<FormInstance>()
const submitting = ref(false)

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const isEdit = computed(() => !!props.task)

const form = reactive({
  project_id: undefined as number | undefined,
  title: '',
  description: '',
  status: 'todo' as 'todo' | 'in_progress' | 'in_review' | 'done',
  priority: 'medium' as 'low' | 'medium' | 'high' | 'critical',
  assignee_id: undefined as number | undefined,
  due_date: '',
  estimated_hours: undefined as number | undefined
})

const rules: FormRules = {
  project_id: [
    { required: true, message: '请选择所属项目', trigger: 'change' }
  ],
  title: [
    { required: true, message: '请输入任务标题', trigger: 'blur' },
    { min: 1, max: 200, message: '长度在 1 到 200 个字符', trigger: 'blur' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ],
  priority: [
    { required: true, message: '请选择优先级', trigger: 'change' }
  ]
}

watch(() => props.task, (newVal) => {
  if (newVal) {
    form.project_id = newVal.project_id
    form.title = newVal.title
    form.description = newVal.description || ''
    form.status = newVal.status
    form.priority = newVal.priority
    form.assignee_id = newVal.assignee_id
    form.due_date = newVal.due_date ? newVal.due_date.split('T')[0] : ''
    form.estimated_hours = newVal.estimated_hours
  } else {
    form.project_id = undefined
    form.title = ''
    form.description = ''
    form.status = 'todo'
    form.priority = 'medium'
    form.assignee_id = undefined
    form.due_date = ''
    form.estimated_hours = undefined
  }
}, { immediate: true })

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      const data = {
        project_id: form.project_id!,
        title: form.title,
        description: form.description || undefined,
        status: form.status,
        priority: form.priority,
        assignee_id: form.assignee_id,
        due_date: form.due_date || undefined,
        estimated_hours: form.estimated_hours
      }

      if (isEdit.value && props.task) {
        await tasksApi.updateTask(props.task.id, data)
        ElMessage.success('更新成功')
      } else {
        await tasksApi.createTask(data)
        ElMessage.success('创建成功')
      }

      emit('success')
    } catch (error) {
      ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
    } finally {
      submitting.value = false
    }
  })
}
</script>

<style scoped>
.task-form {
  padding: 10px 0;
}
</style>
