from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models import UserRole, ProjectStatus, TaskStatus, TaskPriority, NotificationType


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[int] = None
    exp: Optional[datetime] = None


class UserBase(BaseModel):
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    role: UserRole = UserRole.MEMBER


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    avatar_url: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None


class UserLogin(BaseModel):
    username: str
    password: str


class ProjectMember(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    role: str
    joined_at: datetime


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.PLANNING
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    budget: Optional[float] = Field(None, ge=0)


class ProjectCreate(ProjectBase):
    member_ids: Optional[List[int]] = []


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    budget: Optional[float] = Field(None, ge=0)


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str] = None
    status: ProjectStatus
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = None
    owner_id: int
    owner: UserResponse
    members: List[UserResponse]
    created_at: datetime
    updated_at: Optional[datetime] = None
    task_count: int = 0
    completed_task_count: int = 0


class MilestoneBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: datetime


class MilestoneCreate(MilestoneBase):
    pass


class MilestoneResponse(MilestoneBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    completed_at: Optional[datetime] = None
    created_at: datetime


class TaskDependencyBase(BaseModel):
    depends_on_task_id: int
    dependency_type: str = "finish_to_start"


class TaskDependencyCreate(TaskDependencyBase):
    pass


class TaskDependencyResponse(TaskDependencyBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    task_id: int
    created_at: datetime


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_hours: Optional[float] = Field(None, ge=0)
    due_date: Optional[str] = None


class TaskCreate(TaskBase):
    project_id: int
    assignee_id: Optional[int] = None
    parent_task_id: Optional[int] = None
    milestone_id: Optional[int] = None
    dependencies: Optional[List[TaskDependencyCreate]] = []


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[int] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    due_date: Optional[str] = None


class TaskResponse(TaskBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    assignee_id: Optional[int] = None
    assignee: Optional[UserResponse] = None
    created_by: int
    creator: UserResponse
    parent_task_id: Optional[int] = None
    milestone_id: Optional[int] = None
    actual_hours: float = 0
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    subtasks: List['TaskResponse'] = []
    dependencies: List[TaskDependencyResponse] = []


class TimeEntryBase(BaseModel):
    description: Optional[str] = None
    hours: float = Field(..., gt=0)
    date: str


class TimeEntryCreate(TimeEntryBase):
    task_id: int


class TimeEntryUpdate(BaseModel):
    description: Optional[str] = None
    hours: Optional[float] = Field(None, gt=0)
    date: Optional[str] = None


class TimeEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    task_id: int
    task: TaskResponse
    user_id: int
    user: UserResponse
    description: Optional[str] = None
    hours: float
    date: datetime
    created_at: datetime


class DocumentBase(BaseModel):
    name: str


class DocumentCreate(DocumentBase):
    project_id: int


class DocumentResponse(DocumentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    file_path: str
    file_size: int
    mime_type: str
    uploaded_by: int
    uploader: UserResponse
    version: int
    created_at: datetime


class NotificationBase(BaseModel):
    type: NotificationType
    title: str
    message: str


class NotificationCreate(NotificationBase):
    user_id: int
    related_project_id: Optional[int] = None
    related_task_id: Optional[int] = None


class NotificationResponse(NotificationBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    related_project_id: Optional[int] = None
    related_task_id: Optional[int] = None
    is_read: bool
    created_at: datetime


class ProjectStatistics(BaseModel):
    total_projects: int
    active_projects: int
    completed_projects: int
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    overdue_tasks: int


class UserStatistics(BaseModel):
    user_id: int
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    total_hours_logged: float
    projects_count: int


class TimeReportEntry(BaseModel):
    date: datetime
    hours: float
    task_count: int


class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    page_size: int
    total_pages: int
