<template>
  <div class="task-detail">
    <h1>任务详情</h1>
    <el-card>
      <el-empty description="请从任务列表选择任务查看" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.task-detail {
  padding: 20px;
}

.task-detail h1 {
  margin-bottom: 20px;
}
</style>
