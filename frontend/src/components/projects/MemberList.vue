<template>
  <div class="member-list">
    <el-list>
      <el-list-item v-for="member in members" :key="member.id">
        <el-avatar :size="40" :src="member.avatar_url">
          {{ member.first_name[0] }}
        </el-avatar>
        <div class="member-info">
          <div class="member-name">{{ member.first_name }} {{ member.last_name }}</div>
          <div class="member-role">{{ getRoleLabel(member.role) }}</div>
        </div>
      </el-list-item>
    </el-list>
    
    <el-button v-if="canManage" type="primary" text @click="showAddDialog = true">
      + 添加成员
    </el-button>
    
    <el-dialog v-model="showAddDialog" title="添加成员" width="400px">
      <el-select v-model="selectedUser" placeholder="选择用户" style="width: 100%">
        <el-option
          v-for="user in availableUsers"
          :key="user.id"
          :label="`${user.first_name} ${user.last_name} (${user.username})`"
          :value="user.id"
        />
      </el-select>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addMember">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useProjectsStore } from '@/stores/projects'
import { useUsersStore } from '@/stores/users'
import { useAuthStore } from '@/stores/auth'
import type { User } from '@/types'

const props = defineProps<{
  members: User[]
  projectId: number
}>()

const emit = defineEmits<{
  refresh: []
}>()

const projectsStore = useProjectsStore()
const usersStore = useUsersStore()
const authStore = useAuthStore()
const showAddDialog = ref(false)
const selectedUser = ref<number | null>(null)
const allUsers = ref<User[]>([])

const canManage = computed(() => authStore.isProjectManager)

const availableUsers = computed(() => {
  const memberIds = props.members.map(m => m.id)
  return allUsers.value.filter(u => !memberIds.includes(u.id))
})

const getRoleLabel = (role: string) => {
  const labels: Record<string, string> = {
    admin: '管理员',
    project_manager: '项目经理',
    team_lead: '团队负责人',
    member: '成员'
  }
  return labels[role] || role
}

const addMember = async () => {
  if (!selectedUser.value) return
  try {
    await projectsStore.addMember(props.projectId, selectedUser.value)
    ElMessage.success('添加成功')
    showAddDialog.value = false
    selectedUser.value = null
    emit('refresh')
  } catch (error) {
    ElMessage.error('添加失败')
  }
}

onMounted(async () => {
  if (canManage.value) {
    await usersStore.fetchUsers()
    allUsers.value = usersStore.users
  }
})
</script>

<style scoped>
.member-list {
  padding: 10px;
}

.member-info {
  margin-left: 12px;
  flex: 1;
}

.member-name {
  font-weight: 500;
}

.member-role {
  font-size: 12px;
  color: #909399;
}
</style>
