<template>
  <div class="profile">
    <h1>个人资料</h1>
    <el-card>
      <el-form :model="form" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" disabled />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="姓">
          <el-input v-model="form.first_name" />
        </el-form-item>
        <el-form-item label="名">
          <el-input v-model="form.last_name" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSave">保存</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()

const form = reactive({
  username: authStore.user?.username || '',
  email: authStore.user?.email || '',
  first_name: authStore.user?.first_name || '',
  last_name: authStore.user?.last_name || ''
})

const handleSave = () => {
  ElMessage.success('保存成功')
}
</script>

<style scoped>
.profile {
  padding: 20px;
}

.profile h1 {
  margin-bottom: 20px;
}
</style>
