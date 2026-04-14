<template>
  <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
    <el-form-item label="项目名称" prop="name">
      <el-input v-model="form.name" placeholder="请输入项目名称" />
    </el-form-item>
    
    <el-form-item label="项目描述" prop="description">
      <el-input 
        v-model="form.description" 
        type="textarea" 
        :rows="3"
        placeholder="请输入项目描述" 
      />
    </el-form-item>
    
    <el-form-item label="项目状态" prop="status">
      <el-select v-model="form.status" placeholder="选择状态">
        <el-option label="规划中" value="planning" />
        <el-option label="进行中" value="active" />
        <el-option label="暂停" value="on_hold" />
        <el-option label="已完成" value="completed" />
        <el-option label="已取消" value="cancelled" />
      </el-select>
    </el-form-item>
    
    <el-form-item label="开始日期" prop="start_date">
      <el-date-picker
        v-model="form.start_date"
        type="date"
        placeholder="选择开始日期"
        value-format="YYYY-MM-DD"
      />
    </el-form-item>
    
    <el-form-item label="结束日期" prop="end_date">
      <el-date-picker
        v-model="form.end_date"
        type="date"
        placeholder="选择结束日期"
        value-format="YYYY-MM-DD"
      />
    </el-form-item>
    
    <el-form-item label="预算" prop="budget">
      <el-input-number v-model="form.budget" :min="0" :precision="2" />
    </el-form-item>
    
    <el-form-item>
      <el-button type="primary" @click="handleSubmit">保存</el-button>
      <el-button @click="$emit('cancel')">取消</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { Project } from '@/types'

const props = defineProps<{
  project?: Project | null
}>()

const emit = defineEmits<{
  submit: [data: any]
  cancel: []
}>()

const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  description: '',
  status: 'planning',
  start_date: '',
  end_date: '',
  budget: undefined as number | undefined
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 1, max: 200, message: '长度在 1 到 200 个字符', trigger: 'blur' }
  ],
  status: [
    { required: true, message: '请选择项目状态', trigger: 'change' }
  ]
}

watch(() => props.project, (newVal) => {
  if (newVal) {
    form.name = newVal.name
    form.description = newVal.description || ''
    form.status = newVal.status
    form.start_date = newVal.start_date ? newVal.start_date.split('T')[0] : ''
    form.end_date = newVal.end_date ? newVal.end_date.split('T')[0] : ''
    form.budget = newVal.budget
  }
}, { immediate: true })

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate((valid) => {
    if (valid) {
      const data = {
        name: form.name,
        description: form.description || undefined,
        status: form.status,
        start_date: form.start_date || undefined,
        end_date: form.end_date || undefined,
        budget: form.budget
      }
      emit('submit', data)
    }
  })
}
</script>
