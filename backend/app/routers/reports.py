from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.database import get_db
from app.models import (
    User, Project, Task, TimeEntry, TaskStatus, ProjectStatus, UserRole
)
from app.schemas import ProjectStatistics, UserStatistics
from app.auth import get_current_user, check_permissions

router = APIRouter()


@router.get("/projects/statistics", response_model=ProjectStatistics)
async def get_project_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_permissions(current_user, [UserRole.ADMIN, UserRole.PROJECT_MANAGER])
    
    total_projects = db.query(Project).count()
    active_projects = db.query(Project).filter(Project.status == ProjectStatus.ACTIVE).count()
    completed_projects = db.query(Project).filter(Project.status == ProjectStatus.COMPLETED).count()
    
    total_tasks = db.query(Task).count()
    completed_tasks = db.query(Task).filter(Task.status == TaskStatus.DONE).count()
    in_progress_tasks = db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count()
    
    now = datetime.utcnow()
    overdue_tasks = db.query(Task).filter(
        and_(
            Task.due_date < now,
            Task.status != TaskStatus.DONE
        )
    ).count()
    
    return ProjectStatistics(
        total_projects=total_projects,
        active_projects=active_projects,
        completed_projects=completed_projects,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        in_progress_tasks=in_progress_tasks,
        overdue_tasks=overdue_tasks
    )


@router.get("/projects/{project_id}/statistics")
async def get_single_project_statistics(
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
    
    total_tasks = db.query(Task).filter(Task.project_id == project_id).count()
    completed_tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == TaskStatus.DONE
    ).count()
    in_progress_tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == TaskStatus.IN_PROGRESS
    ).count()
    todo_tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == TaskStatus.TODO
    ).count()
    
    now = datetime.utcnow()
    overdue_tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.due_date < now,
        Task.status != TaskStatus.DONE
    ).count()
    
    total_estimated_hours = db.query(func.sum(Task.estimated_hours)).filter(
        Task.project_id == project_id
    ).scalar() or 0
    
    total_actual_hours = db.query(func.sum(Task.actual_hours)).filter(
        Task.project_id == project_id
    ).scalar() or 0
    
    total_time_logged = db.query(func.sum(TimeEntry.hours)).join(Task).filter(
        Task.project_id == project_id
    ).scalar() or 0
    
    completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "status": project.status.value,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "todo_tasks": todo_tasks,
        "overdue_tasks": overdue_tasks,
        "completion_percentage": round(completion_percentage, 2),
        "total_estimated_hours": round(total_estimated_hours, 2),
        "total_actual_hours": round(total_actual_hours, 2),
        "total_time_logged": round(total_time_logged, 2),
        "member_count": len(project.members),
        "start_date": project.start_date,
        "end_date": project.end_date,
        "budget": project.budget
    }


@router.get("/users/statistics", response_model=List[UserStatistics])
async def get_users_statistics(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_permissions(current_user, [UserRole.ADMIN, UserRole.PROJECT_MANAGER])
    
    users = db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()
    
    statistics = []
    for user in users:
        total_tasks = db.query(Task).filter(
            Task.assignee_id == user.id
        ).count()
        
        completed_tasks = db.query(Task).filter(
            Task.assignee_id == user.id,
            Task.status == TaskStatus.DONE
        ).count()
        
        in_progress_tasks = db.query(Task).filter(
            Task.assignee_id == user.id,
            Task.status == TaskStatus.IN_PROGRESS
        ).count()
        
        total_hours = db.query(func.sum(TimeEntry.hours)).filter(
            TimeEntry.user_id == user.id
        ).scalar() or 0
        
        projects_count = len(user.projects) + len(user.owned_projects)
        
        statistics.append(UserStatistics(
            user_id=user.id,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            in_progress_tasks=in_progress_tasks,
            total_hours_logged=round(total_hours, 2),
            projects_count=projects_count
        ))
    
    return statistics


@router.get("/users/{user_id}/statistics", response_model=UserStatistics)
async def get_single_user_statistics(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.id != user_id and current_user.role not in [UserRole.ADMIN, UserRole.PROJECT_MANAGER]:
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
    
    total_tasks = db.query(Task).filter(Task.assignee_id == user_id).count()
    
    completed_tasks = db.query(Task).filter(
        Task.assignee_id == user_id,
        Task.status == TaskStatus.DONE
    ).count()
    
    in_progress_tasks = db.query(Task).filter(
        Task.assignee_id == user_id,
        Task.status == TaskStatus.IN_PROGRESS
    ).count()
    
    total_hours = db.query(func.sum(TimeEntry.hours)).filter(
        TimeEntry.user_id == user_id
    ).scalar() or 0
    
    projects_count = len(user.projects) + len(user.owned_projects)
    
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_time_entries = db.query(
        func.date(TimeEntry.date).label("date"),
        func.sum(TimeEntry.hours).label("hours")
    ).filter(
        TimeEntry.user_id == user_id,
        TimeEntry.date >= thirty_days_ago
    ).group_by(func.date(TimeEntry.date)).all()
    
    return UserStatistics(
        user_id=user_id,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        in_progress_tasks=in_progress_tasks,
        total_hours_logged=round(total_hours, 2),
        projects_count=projects_count
    )


@router.get("/time/summary")
async def get_time_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    project_id: Optional[int] = None,
    user_id: Optional[int] = None,
    group_by: str = Query("day", regex="^(day|week|month|user|project)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.PROJECT_MANAGER]:
        user_id = current_user.id
    
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    query = db.query(TimeEntry).filter(
        TimeEntry.date >= start_date,
        TimeEntry.date <= end_date
    )
    
    if user_id:
        query = query.filter(TimeEntry.user_id == user_id)
    if project_id:
        query = query.join(Task).filter(Task.project_id == project_id)
    
    total_hours = query.with_entities(func.sum(TimeEntry.hours)).scalar() or 0
    total_entries = query.count()
    
    if group_by == "day":
        breakdown = db.query(
            func.date(TimeEntry.date).label("period"),
            func.sum(TimeEntry.hours).label("hours"),
            func.count(TimeEntry.id).label("entries")
        ).filter(
            TimeEntry.date >= start_date,
            TimeEntry.date <= end_date
        )
        if user_id:
            breakdown = breakdown.filter(TimeEntry.user_id == user_id)
        if project_id:
            breakdown = breakdown.join(Task).filter(Task.project_id == project_id)
        breakdown = breakdown.group_by(func.date(TimeEntry.date)).all()
    
    elif group_by == "user":
        breakdown = db.query(
            User.username.label("period"),
            func.sum(TimeEntry.hours).label("hours"),
            func.count(TimeEntry.id).label("entries")
        ).join(TimeEntry).filter(
            TimeEntry.date >= start_date,
            TimeEntry.date <= end_date
        )
        if project_id:
            breakdown = breakdown.join(Task).filter(Task.project_id == project_id)
        breakdown = breakdown.group_by(User.id).all()
    
    elif group_by == "project":
        breakdown = db.query(
            Project.name.label("period"),
            func.sum(TimeEntry.hours).label("hours"),
            func.count(TimeEntry.id).label("entries")
        ).join(Task, TimeEntry.task_id == Task.id).join(Project).filter(
            TimeEntry.date >= start_date,
            TimeEntry.date <= end_date
        )
        if user_id:
            breakdown = breakdown.filter(TimeEntry.user_id == user_id)
        breakdown = breakdown.group_by(Project.id).all()
    
    else:
        breakdown = []
    
    return {
        "total_hours": round(total_hours, 2),
        "total_entries": total_entries,
        "start_date": start_date,
        "end_date": end_date,
        "group_by": group_by,
        "breakdown": [
            {"period": str(b.period), "hours": round(b.hours, 2), "entries": b.entries}
            for b in breakdown
        ]
    }
