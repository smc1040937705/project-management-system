import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { public: true }
    },
    {
      path: '/',
      name: 'layout',
      component: () => import('@/layouts/MainLayout.vue'),
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue')
        },
        {
          path: 'projects',
          name: 'projects',
          component: () => import('@/views/projects/ProjectListView.vue')
        },
        {
          path: 'projects/:id',
          name: 'project-detail',
          component: () => import('@/views/projects/ProjectDetailView.vue')
        },
        {
          path: 'projects/:id/edit',
          name: 'project-edit',
          component: () => import('@/views/projects/ProjectEditView.vue')
        },
        {
          path: 'tasks',
          name: 'tasks',
          component: () => import('@/views/tasks/TaskListView.vue')
        },
        {
          path: 'tasks/:id',
          name: 'task-detail',
          component: () => import('@/views/tasks/TaskDetailView.vue')
        },
        {
          path: 'time-entries',
          name: 'time-entries',
          component: () => import('@/views/time/TimeEntryListView.vue')
        },
        {
          path: 'documents',
          name: 'documents',
          component: () => import('@/views/documents/DocumentListView.vue')
        },
        {
          path: 'reports',
          name: 'reports',
          component: () => import('@/views/reports/ReportView.vue')
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('@/views/users/UserListView.vue'),
          meta: { adminOnly: true }
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('@/views/ProfileView.vue')
        },
        {
          path: 'notifications',
          name: 'notifications',
          component: () => import('@/views/notifications/NotificationListView.vue')
        }
      ]
    }
  ]
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (!to.meta.public && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.adminOnly && !authStore.isAdmin) {
    next('/')
  } else {
    next()
  }
})

export default router
