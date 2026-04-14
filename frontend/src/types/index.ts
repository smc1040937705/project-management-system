export interface User {
  id: number
  email: string
  username: string
  first_name: string
  last_name: string
  role: 'admin' | 'project_manager' | 'team_lead' | 'member'
  is_active: boolean
  avatar_url?: string
  created_at: string
  last_login?: string
}

export interface UserLogin {
  username: string
  password: string
}

export interface UserCreate {
  email: string
  username: string
  password: string
  first_name: string
  last_name: string
  role: 'admin' | 'project_manager' | 'team_lead' | 'member'
}

export interface UserUpdate {
  email?: string
  first_name?: string
  last_name?: string
  role?: 'admin' | 'project_manager' | 'team_lead' | 'member'
  is_active?: boolean
  avatar_url?: string
}

export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface Project {
  id: number
  name: string
  description?: string
  status: 'planning' | 'active' | 'on_hold' | 'completed' | 'cancelled'
  owner_id: number
  owner: User
  members: User[]
  start_date?: string
  end_date?: string
  budget?: number
  created_at: string
  updated_at?: string
  task_count: number
  completed_task_count: number
}

export interface ProjectCreate {
  name: string
  description?: string
  status: 'planning' | 'active' | 'on_hold' | 'completed' | 'cancelled'
  start_date?: string
  end_date?: string
  budget?: number
  member_ids?: number[]
}

export interface ProjectUpdate {
  name?: string
  description?: string
  status?: 'planning' | 'active' | 'on_hold' | 'completed' | 'cancelled'
  start_date?: string
  end_date?: string
  budget?: number
}

export interface Task {
  id: number
  project_id: number
  title: string
  description?: string
  status: 'todo' | 'in_progress' | 'in_review' | 'done'
  priority: 'low' | 'medium' | 'high' | 'critical'
  assignee_id?: number
  assignee?: User
  created_by: number
  creator: User
  parent_task_id?: number
  milestone_id?: number
  estimated_hours?: number
  actual_hours: number
  due_date?: string
  completed_at?: string
  created_at: string
  updated_at?: string
  subtasks: Task[]
  dependencies: TaskDependency[]
}

export interface TaskCreate {
  project_id: number
  title: string
  description?: string
  status: 'todo' | 'in_progress' | 'in_review' | 'done'
  priority: 'low' | 'medium' | 'high' | 'critical'
  assignee_id?: number
  parent_task_id?: number
  milestone_id?: number
  estimated_hours?: number
  due_date?: string
  dependencies?: TaskDependencyCreate[]
}

export interface TaskUpdate {
  title?: string
  description?: string
  status?: 'todo' | 'in_progress' | 'in_review' | 'done'
  priority?: 'low' | 'medium' | 'high' | 'critical'
  assignee_id?: number | null
  estimated_hours?: number
  due_date?: string | null
}

export interface TaskDependency {
  id: number
  task_id: number
  depends_on_task_id: number
  dependency_type: string
  created_at: string
}

export interface TaskDependencyCreate {
  depends_on_task_id: number
  dependency_type?: string
}

export interface TimeEntry {
  id: number
  task_id: number
  task: Task
  user_id: number
  user: User
  description?: string
  hours: number
  date: string
  created_at: string
}

export interface TimeEntryCreate {
  task_id: number
  description?: string
  hours: number
  date: string
}

export interface TimeEntryUpdate {
  description?: string
  hours?: number
  date?: string
}

export interface Notification {
  id: number
  user_id: number
  type: 'task_assigned' | 'task_completed' | 'project_update' | 'deadline_reminder' | 'mention'
  title: string
  message: string
  related_project_id?: number
  related_task_id?: number
  is_read: boolean
  created_at: string
}

export interface NotificationCreate {
  user_id: number
  type: 'task_assigned' | 'task_completed' | 'project_update' | 'deadline_reminder' | 'mention'
  title: string
  message: string
  related_project_id?: number
  related_task_id?: number
}

export interface Document {
  id: number
  project_id: number
  name: string
  file_path: string
  file_size: number
  mime_type: string
  uploaded_by: number
  uploader: User
  version: number
  created_at: string
}

export interface DocumentCreate {
  project_id: number
  name: string
}

export interface ProjectStatistics {
  total_projects: number
  active_projects: number
  completed_projects: number
  total_tasks: number
  completed_tasks: number
  in_progress_tasks: number
  overdue_tasks: number
}

export interface UserStatistics {
  user_id: number
  total_tasks: number
  completed_tasks: number
  in_progress_tasks: number
  total_hours_logged: number
  projects_count: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}
