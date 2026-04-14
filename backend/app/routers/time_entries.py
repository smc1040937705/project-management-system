from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.database import get_db
from app.models import User, Task, TimeEntry, UserRole
from app.schemas import TimeEntryCreate, TimeEntryUpdate, TimeEntryResponse
from app.auth import get_current_user, check_permissions

def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

router = APIRouter()


@router.get("", response_model=List[TimeEntryResponse])
async def list_time_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    task_id: Optional[int] = None,
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(TimeEntry).options(
        joinedload(TimeEntry.user),
        joinedload(TimeEntry.task)
    )
    
    if current_user.role not in [UserRole.ADMIN, UserRole.PROJECT_MANAGER]:
        query = query.filter(TimeEntry.user_id == current_user.id)
    elif user_id:
        query = query.filter(TimeEntry.user_id == user_id)
    
    if task_id:
        query = query.filter(TimeEntry.task_id == task_id)
    if start_date:
        start_dt = parse_date(start_date)
        if start_dt:
            query = query.filter(TimeEntry.date >= start_dt)
    if end_date:
        end_dt = parse_date(end_date)
        if end_dt:
            query = query.filter(TimeEntry.date <= end_dt)
    
    entries = query.order_by(TimeEntry.date.desc()).offset(skip).limit(limit).all()
    return entries


@router.get("/summary")
async def get_time_summary(
    user_id: Optional[int] = None,
    project_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.PROJECT_MANAGER]:
        user_id = current_user.id
    
    query = db.query(func.sum(TimeEntry.hours).label("total_hours"))
    
    if user_id:
        query = query.filter(TimeEntry.user_id == user_id)
    if project_id:
        query = query.join(Task).filter(Task.project_id == project_id)
    if start_date:
        query = query.filter(TimeEntry.date >= start_date)
    if end_date:
        query = query.filter(TimeEntry.date <= end_date)
    
    result = query.first()
    total_hours = result.total_hours or 0
    
    daily_query = db.query(
        func.date(TimeEntry.date).label("date"),
        func.sum(TimeEntry.hours).label("hours"),
        func.count(TimeEntry.id).label("entry_count")
    )
    
    if user_id:
        daily_query = daily_query.filter(TimeEntry.user_id == user_id)
    if project_id:
        daily_query = daily_query.join(Task).filter(Task.project_id == project_id)
    if start_date:
        daily_query = daily_query.filter(TimeEntry.date >= start_date)
    if end_date:
        daily_query = daily_query.filter(TimeEntry.date <= end_date)
    
    daily_data = daily_query.group_by(func.date(TimeEntry.date)).all()
    
    return {
        "total_hours": total_hours,
        "daily_breakdown": [
            {"date": d.date, "hours": d.hours, "entry_count": d.entry_count}
            for d in daily_data
        ]
    }


@router.get("/{entry_id}", response_model=TimeEntryResponse)
async def get_time_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    entry = db.query(TimeEntry).options(
        joinedload(TimeEntry.user),
        joinedload(TimeEntry.task)
    ).filter(TimeEntry.id == entry_id).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time entry not found"
        )
    
    if (current_user.role not in [UserRole.ADMIN, UserRole.PROJECT_MANAGER] and
        entry.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return entry


@router.post("", response_model=TimeEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_time_entry(
    entry_data: TimeEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == entry_data.task_id).first()
    
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
    
    new_entry = TimeEntry(
        task_id=entry_data.task_id,
        user_id=current_user.id,
        description=entry_data.description,
        hours=entry_data.hours,
        date=parse_date(entry_data.date) or datetime.utcnow()
    )
    
    task.actual_hours = (task.actual_hours or 0) + entry_data.hours
    
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    
    new_entry.user = current_user
    new_entry.task = task
    
    return new_entry


@router.put("/{entry_id}", response_model=TimeEntryResponse)
async def update_time_entry(
    entry_id: int,
    entry_data: TimeEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    entry = db.query(TimeEntry).options(
        joinedload(TimeEntry.user),
        joinedload(TimeEntry.task)
    ).filter(TimeEntry.id == entry_id).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time entry not found"
        )
    
    if (current_user.role not in [UserRole.ADMIN, UserRole.PROJECT_MANAGER] and
        entry.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if entry_data.hours is not None and entry_data.hours != entry.hours:
        hours_diff = entry_data.hours - entry.hours
        entry.task.actual_hours = (entry.task.actual_hours or 0) + hours_diff
        entry.hours = entry_data.hours
    
    if entry_data.description is not None:
        entry.description = entry_data.description
    if entry_data.date is not None:
        entry.date = parse_date(entry_data.date) or entry.date
    
    db.commit()
    db.refresh(entry)
    
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_time_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time entry not found"
        )
    
    if (current_user.role not in [UserRole.ADMIN, UserRole.PROJECT_MANAGER] and
        entry.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    entry.task.actual_hours = (entry.task.actual_hours or 0) - entry.hours
    
    db.delete(entry)
    db.commit()
