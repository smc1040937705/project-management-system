from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import User, Project, ProjectStatus, UserRole, TaskStatus
from app.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    MilestoneCreate, MilestoneResponse
)
from app.auth import get_current_user, check_permissions

def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

router = APIRouter()


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[ProjectStatus] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Project)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.PROJECT_MANAGER]:
        query = query.filter(
            (Project.owner_id == current_user.id) |
            (Project.members.any(id=current_user.id))
        )
    
    if status:
        query = query.filter(Project.status == status)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Project.name.ilike(search_filter)) |
            (Project.description.ilike(search_filter))
        )
    
    projects = query.offset(skip).limit(limit).all()
    
    for project in projects:
        project.task_count = len(project.tasks)
        project.completed_task_count = len([t for t in project.tasks if t.status == TaskStatus.DONE])
    
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if (current_user.role not in [UserRole.ADMIN, UserRole.PROJECT_MANAGER] and
        project.owner_id != current_user.id and
        current_user.id not in [m.id for m in project.members]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    project.task_count = len(project.tasks)
    project.completed_task_count = len([t for t in project.tasks if t.status == TaskStatus.DONE])
    
    return project


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_permissions(current_user, [UserRole.ADMIN, UserRole.PROJECT_MANAGER, UserRole.TEAM_LEAD, UserRole.MEMBER])
    
    new_project = Project(
        name=project_data.name,
        description=project_data.description,
        status=project_data.status,
        owner_id=current_user.id,
        start_date=parse_date(project_data.start_date),
        end_date=parse_date(project_data.end_date),
        budget=project_data.budget
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    if project_data.member_ids:
        members = db.query(User).filter(User.id.in_(project_data.member_ids)).all()
        new_project.members = members
        db.commit()
    
    new_project.task_count = 0
    new_project.completed_task_count = 0
    
    return new_project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if (current_user.role not in [UserRole.ADMIN, UserRole.PROJECT_MANAGER] and
        project.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if project_data.name:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    if project_data.status:
        project.status = project_data.status
    if project_data.start_date is not None:
        project.start_date = parse_date(project_data.start_date)
    if project_data.end_date is not None:
        project.end_date = parse_date(project_data.end_date)
    if project_data.budget is not None:
        project.budget = project_data.budget
    
    db.commit()
    db.refresh(project)
    
    project.task_count = len(project.tasks)
    project.completed_task_count = len([t for t in project.tasks if t.status == TaskStatus.DONE])
    
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db.delete(project)
    db.commit()


@router.post("/{project_id}/members/{user_id}", response_model=ProjectResponse)
async def add_project_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if (current_user.role not in [UserRole.ADMIN, UserRole.PROJECT_MANAGER] and
        project.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user in project.members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this project"
        )
    
    project.members.append(user)
    db.commit()
    db.refresh(project)
    
    return project


@router.delete("/{project_id}/members/{user_id}", response_model=ProjectResponse)
async def remove_project_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if (current_user.role not in [UserRole.ADMIN, UserRole.PROJECT_MANAGER] and
        project.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or user not in project.members:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this project"
        )
    
    project.members.remove(user)
    db.commit()
    db.refresh(project)
    
    return project
