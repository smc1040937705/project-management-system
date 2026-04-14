from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Project, Task, TaskStatus, TaskPriority, UserRole, TaskDependency
from app.schemas import (
    TaskCreate, TaskUpdate, TaskResponse,
    TaskDependencyCreate, TaskDependencyResponse
)

def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None
from app.auth import get_current_user, check_permissions

router = APIRouter()


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    project_id: Optional[int] = None,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    assignee_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Task)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.PROJECT_MANAGER]:
        user_project_ids = [p.id for p in current_user.projects] + [p.id for p in current_user.owned_projects]
        if user_project_ids:
            query = query.filter(Task.project_id.in_(user_project_ids))
    
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Task.title.ilike(search_filter)) |
            (Task.description.ilike(search_filter))
        )
    
    tasks = query.offset(skip).limit(limit).all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    project = task.project
    if (current_user.role not in [UserRole.ADMIN, UserRole.PROJECT_MANAGER] and
        project.owner_id != current_user.id and
        current_user.id not in [m.id for m in project.members] and
        task.assignee_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return task


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == task_data.project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 检查权限：所有登录用户都可以创建任务（简化权限控制）
    # is_member = current_user.id in [m.id for m in project.members]
    # if (current_user.role not in [UserRole.ADMIN, UserRole.PROJECT_MANAGER] and
    #     project.owner_id != current_user.id and
    #     not is_member):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Not enough permissions"
    #     )
    
    if task_data.assignee_id:
        assignee = db.query(User).filter(User.id == task_data.assignee_id).first()
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignee not found"
            )
    
    new_task = Task(
        project_id=task_data.project_id,
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        priority=task_data.priority,
        assignee_id=task_data.assignee_id,
        created_by=current_user.id,
        parent_task_id=task_data.parent_task_id,
        milestone_id=task_data.milestone_id,
        estimated_hours=task_data.estimated_hours,
        due_date=parse_date(task_data.due_date)
    )
    
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    if task_data.dependencies:
        for dep in task_data.dependencies:
            dependency = TaskDependency(
                task_id=new_task.id,
                depends_on_task_id=dep.depends_on_task_id,
                dependency_type=dep.dependency_type
            )
            db.add(dependency)
        db.commit()
        db.refresh(new_task)
    
    return new_task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    project = task.project
    if (current_user.role not in [UserRole.ADMIN, UserRole.PROJECT_MANAGER] and
        project.owner_id != current_user.id and
        task.assignee_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if task_data.title:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.status:
        task.status = task_data.status
        if task_data.status == TaskStatus.DONE:
            task.completed_at = datetime.utcnow()
    if task_data.priority:
        task.priority = task_data.priority
    if task_data.assignee_id is not None:
        if task_data.assignee_id:
            assignee = db.query(User).filter(User.id == task_data.assignee_id).first()
            if not assignee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assignee not found"
                )
        task.assignee_id = task_data.assignee_id
    if task_data.estimated_hours is not None:
        task.estimated_hours = task_data.estimated_hours
    if task_data.due_date is not None:
        task.due_date = parse_date(task_data.due_date)
    
    db.commit()
    db.refresh(task)
    
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    project = task.project
    if (current_user.role not in [UserRole.ADMIN, UserRole.PROJECT_MANAGER] and
        project.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db.delete(task)
    db.commit()


@router.post("/{task_id}/dependencies", response_model=TaskDependencyResponse)
async def add_task_dependency(
    task_id: int,
    dependency_data: TaskDependencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    depends_on_task = db.query(Task).filter(Task.id == dependency_data.depends_on_task_id).first()
    
    if not depends_on_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dependency task not found"
        )
    
    if depends_on_task.project_id != task.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tasks must belong to the same project"
        )
    
    if task_id == dependency_data.depends_on_task_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task cannot depend on itself"
        )
    
    existing = db.query(TaskDependency).filter(
        TaskDependency.task_id == task_id,
        TaskDependency.depends_on_task_id == dependency_data.depends_on_task_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dependency already exists"
        )
    
    dependency = TaskDependency(
        task_id=task_id,
        depends_on_task_id=dependency_data.depends_on_task_id,
        dependency_type=dependency_data.dependency_type
    )
    
    db.add(dependency)
    db.commit()
    db.refresh(dependency)
    
    return dependency


@router.delete("/{task_id}/dependencies/{dependency_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_task_dependency(
    task_id: int,
    dependency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dependency = db.query(TaskDependency).filter(
        TaskDependency.id == dependency_id,
        TaskDependency.task_id == task_id
    ).first()
    
    if not dependency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dependency not found"
        )
    
    db.delete(dependency)
    db.commit()
