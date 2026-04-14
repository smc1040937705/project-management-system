<template>
  <el-dialog
    :title="isEdit ? '编辑工时记录' : '记录工时'"
    v-model="dialogVisible"
    width="500px"
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      class="time-entry-form"
    >
      <el-form-item label="所属项目" prop="project_id">
        <el-select 
          v-model="form.project_id" 
          placeholder="选择项目" 
          style="width: 100%"
          @change="handleProjectChange"
        >
          <el-option
            v-for="project in projects"
            :key="project.id"
            :label="project.name"
            :value="project.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="任务" prop="task_id">
        <el-select 
          v-model="form.task_id" 
          placeholder="选择任务" 
          style="width: 100%"
          :disabled="!form.project_id"
        >
          <el-option
            v-for="task in filteredTasks"
            :key="task.id"
            :label="task.title"
            :value="task.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="工作日期" prop="date">
        <el-date-picker
          v-model="form.date"
          type="date"
          placeholder="选择日期"
          value-format="YYYY-MM-DD"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="工时" prop="hours">
        <el-input-number
          v-model="form.hours"
          :min="0.1"
          :max="24"
          :precision="1"
          :step="0.5"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="工作内容" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请描述本次工作的内容"
        />
      </el-form-item>
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
import { timeEntriesApi } from '@/api'
import type { TimeEntry, Project, Task } from '@/types'

const props = defineProps<{
  visible: boolean
  timeEntry: TimeEntry | null
  projects: Project[]
  tasks: Task[]
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

const isEdit = computed(() => !!props.timeEntry)

const filteredTasks = computed(() => {
  if (!form.project_id) return []
  return props.tasks.filter(t => t.project_id === form.project_id)
})

const form = reactive({
  project_id: undefined as number | undefined,
  task_id: undefined as number | undefined,
  date: new Date().toISOString().split('T')[0],
  hours: 8,
  description: ''
})

const rules: FormRules = {
  project_id: [
    { required: true, message: '请选择项目', trigger: 'change' }
  ],
  task_id: [
    { required: true, message: '请选择任务', trigger: 'change' }
  ],
  date: [
    { required: true, message: '请选择日期', trigger: 'change' }
  ],
  hours: [
    { required: true, message: '请输入工时', trigger: 'blur' },
    { type: 'number', min: 0.1, max: 24, message: '工时必须大于0且不超过24小时', trigger: 'blur' }
  ],
  description: [
    { max: 500, message: '长度不超过500个字符', trigger: 'blur' }
  ]
}

watch(() => props.timeEntry, (newVal) => {
  if (newVal) {
    form.project_id = newVal.task?.project_id
    form.task_id = newVal.task_id
    form.date = newVal.date.split('T')[0]
    form.hours = newVal.hours
    form.description = newVal.description || ''
  } else {
    form.project_id = undefined
    form.task_id = undefined
    form.date = new Date().toISOString().split('T')[0]
    form.hours = 8
    form.description = ''
  }
}, { immediate: true })

const handleProjectChange = () => {
  form.task_id = undefined
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      const data = {
        task_id: form.task_id!,
        date: form.date,
        hours: form.hours,
        description: form.description || undefined
      }

      if (isEdit.value && props.timeEntry) {
        await timeEntriesApi.updateTimeEntry(props.timeEntry.id, data)
        ElMessage.success('更新成功')
      } else {
        await timeEntriesApi.createTimeEntry(data)
        ElMessage.success('记录成功')
      }

      emit('success')
    } catch (error) {
      ElMessage.error(isEdit.value ? '更新失败' : '记录失败')
    } finally {
      submitting.value = false
    }
  })
}
</script>

<style scoped>
.time-entry-form {
  padding: 10px 0;
}
</style>
