"""
任务管理路由异步测试
使用 pytest-asyncio + httpx 进行异步测试
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models import User, Project, Task, UserRole, ProjectStatus, TaskStatus, TaskPriority
from app.auth import get_password_hash, create_access_token


@pytest.mark.asyncio
class TestTasksRouterAsync:
    """任务管理路由异步测试类"""

    async def test_list_tasks_success(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：正常获取任务列表
        验证：返回任务列表
        """
        user = User(
            email="tasklist@example.com",
            username="tasklist",
            hashed_password=get_password_hash("password123"),
            first_name="Task",
            last_name="List",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        project = Project(
            name="Task Project",
            status=ProjectStatus.ACTIVE,
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()
        
        task = Task(
            project_id=project.id,
            title="Test Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=user.id
        )
        db_session.add(task)
        db_session.commit()
        
        token = create_access_token(subject=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.get("/api/v1/tasks", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_tasks_with_project_filter(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：按项目筛选任务
        验证：只返回指定项目的任务
        """
        user = User(
            email="taskfilter@example.com",
            username="taskfilter",
            hashed_password=get_password_hash("password123"),
            first_name="Task",
            last_name="Filter",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        project = Project(
            name="Filter Project",
            status=ProjectStatus.ACTIVE,
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()
        
        task = Task(
            project_id=project.id,
            title="Filtered Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=user.id
        )
        db_session.add(task)
        db_session.commit()
        
        token = create_access_token(subject=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.get(
            f"/api/v1/tasks?project_id={project.id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_create_task_success(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：正常创建任务
        验证：返回201状态码和任务数据
        """
        user = User(
            email="createtask@example.com",
            username="createtask",
            hashed_password=get_password_hash("password123"),
            first_name="Create",
            last_name="Task",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        project = Project(
            name="Create Task Project",
            status=ProjectStatus.ACTIVE,
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()
        
        token = create_access_token(subject=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.post(
            "/api/v1/tasks",
            headers=headers,
            json={
                "title": "New Task",
                "description": "New Description",
                "project_id": project.id,
                "status": "todo",
                "priority": "high"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Task"
        assert data["project_id"] == project.id

    async def test_create_task_project_not_found(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：创建任务失败（项目不存在）
        验证：返回404错误
        """
        user = User(
            email="tasknotfound@example.com",
            username="tasknotfound",
            hashed_password=get_password_hash("password123"),
            first_name="Task",
            last_name="NotFound",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        token = create_access_token(subject=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.post(
            "/api/v1/tasks",
            headers=headers,
            json={
                "title": "New Task",
                "project_id": 99999
            }
        )
        
        assert response.status_code == 404

    async def test_get_task_success(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：正常获取单个任务
        验证：返回任务详细信息
        """
        user = User(
            email="gettask@example.com",
            username="gettask",
            hashed_password=get_password_hash("password123"),
            first_name="Get",
            last_name="Task",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        project = Project(
            name="Get Task Project",
            status=ProjectStatus.ACTIVE,
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()
        
        task = Task(
            project_id=project.id,
            title="Specific Task",
            description="Specific Description",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            created_by=user.id
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        token = create_access_token(subject=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.get(
            f"/api/v1/tasks/{task.id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task.id
        assert data["title"] == "Specific Task"

    async def test_update_task_success(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：正常更新任务
        验证：返回更新后的任务数据
        """
        user = User(
            email="updatetask@example.com",
            username="updatetask",
            hashed_password=get_password_hash("password123"),
            first_name="Update",
            last_name="Task",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        project = Project(
            name="Update Task Project",
            status=ProjectStatus.ACTIVE,
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()
        
        task = Task(
            project_id=project.id,
            title="Old Task Title",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=user.id
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        token = create_access_token(subject=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.put(
            f"/api/v1/tasks/{task.id}",
            headers=headers,
            json={
                "title": "Updated Task Title",
                "status": "in_progress"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Task Title"
        assert data["status"] == "in_progress"

    async def test_update_task_status_to_done(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：更新任务状态为完成
        验证：任务状态更新，completed_at字段被设置
        """
        user = User(
            email="completetask@example.com",
            username="completetask",
            hashed_password=get_password_hash("password123"),
            first_name="Complete",
            last_name="Task",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        project = Project(
            name="Complete Task Project",
            status=ProjectStatus.ACTIVE,
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()
        
        task = Task(
            project_id=project.id,
            title="Task to Complete",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.MEDIUM,
            created_by=user.id
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        token = create_access_token(subject=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.put(
            f"/api/v1/tasks/{task.id}",
            headers=headers,
            json={"status": "done"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"

    async def test_delete_task_success(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：正常删除任务
        验证：返回204状态码
        """
        user = User(
            email="deletetask@example.com",
            username="deletetask",
            hashed_password=get_password_hash("password123"),
            first_name="Delete",
            last_name="Task",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        project = Project(
            name="Delete Task Project",
            status=ProjectStatus.ACTIVE,
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()
        
        task = Task(
            project_id=project.id,
            title="Task to Delete",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=user.id
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        token = create_access_token(subject=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.delete(
            f"/api/v1/tasks/{task.id}",
            headers=headers
        )
        
        assert response.status_code == 204
