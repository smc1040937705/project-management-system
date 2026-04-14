import pytest
from httpx import AsyncClient
from app.models import TaskStatus, TaskPriority


class TestTasks:
    @pytest.mark.asyncio
    async def test_list_tasks_success(self, authenticated_client: AsyncClient, db_session, test_user, test_project):
        """测试获取任务列表成功"""
        from app.models import Task
        task = Task(
            title="Test Task",
            description="Test Description",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            project_id=test_project.id,
            created_by=test_user.id,
            assignee_id=test_user.id
        )
        db_session.add(task)
        db_session.commit()
        
        response = await authenticated_client.get("/api/v1/tasks")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_list_tasks_filter_by_project(self, authenticated_client: AsyncClient, db_session, test_user, test_project):
        """测试按项目过滤任务"""
        from app.models import Project, Task
        project2 = Project(
            name="Second Project",
            status="active",
            owner_id=test_user.id
        )
        db_session.add(project2)
        db_session.commit()
        
        task1 = Task(
            title="Task 1",
            project_id=test_project.id,
            created_by=test_user.id
        )
        task2 = Task(
            title="Task 2",
            project_id=project2.id,
            created_by=test_user.id
        )
        db_session.add_all([task1, task2])
        db_session.commit()
        
        response = await authenticated_client.get(f"/api/v1/tasks?project_id={test_project.id}")
        
        assert response.status_code == 200
        data = response.json()
        for task in data:
            assert task["project_id"] == test_project.id

    @pytest.mark.asyncio
    async def test_list_tasks_filter_by_status(self, authenticated_client: AsyncClient, db_session, test_user, test_project):
        """测试按状态过滤任务"""
        from app.models import Task
        task1 = Task(
            title="Task TODO",
            status=TaskStatus.TODO,
            project_id=test_project.id,
            created_by=test_user.id
        )
        task2 = Task(
            title="Task IN_PROGRESS",
            status=TaskStatus.IN_PROGRESS,
            project_id=test_project.id,
            created_by=test_user.id
        )
        db_session.add_all([task1, task2])
        db_session.commit()
        
        response = await authenticated_client.get("/api/v1/tasks?status=todo")
        
        assert response.status_code == 200
        data = response.json()
        for task in data:
            assert task["status"] == "todo"

    @pytest.mark.asyncio
    async def test_list_tasks_filter_by_assignee(self, authenticated_client: AsyncClient, db_session, test_user, test_project):
        """测试按负责人过滤任务"""
        from app.models import User, Task
        other_user = User(
            email="other@example.com",
            username="other",
            hashed_password="hash",
            first_name="Other",
            last_name="User",
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()
        
        task1 = Task(
            title="Task for test_user",
            project_id=test_project.id,
            created_by=test_user.id,
            assignee_id=test_user.id
        )
        task2 = Task(
            title="Task for other_user",
            project_id=test_project.id,
            created_by=test_user.id,
            assignee_id=other_user.id
        )
        db_session.add_all([task1, task2])
        db_session.commit()
        
        response = await authenticated_client.get(f"/api/v1/tasks?assignee_id={test_user.id}")
        
        assert response.status_code == 200
        data = response.json()
        for task in data:
            assert task["assignee_id"] == test_user.id

    @pytest.mark.asyncio
    async def test_get_task_success(self, authenticated_client: AsyncClient, db_session, test_user, test_project):
        """测试获取单个任务成功"""
        from app.models import Task
        task = Task(
            title="Test Task",
            description="Test Description",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            project_id=test_project.id,
            created_by=test_user.id,
            assignee_id=test_user.id
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        response = await authenticated_client.get(f"/api/v1/tasks/{task.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task.id
        assert data["title"] == task.title
        assert data["description"] == task.description
        assert data["priority"] == "high"

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, authenticated_client: AsyncClient):
        """测试获取任务失败 - 任务不存在"""
        response = await authenticated_client.get("/api/v1/tasks/99999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    @pytest.mark.asyncio
    async def test_create_task_success(self, authenticated_client: AsyncClient, test_project):
        """测试创建任务成功"""
        task_data = {
            "title": "New Task",
            "description": "New Task Description",
            "status": "todo",
            "priority": "medium",
            "project_id": test_project.id,
            "assignee_id": None,
            "due_date": "2024-12-31T23:59:59Z"
        }
        
        response = await authenticated_client.post(
            "/api/v1/tasks",
            json=task_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["description"] == task_data["description"]
        assert data["status"] == "todo"

    @pytest.mark.asyncio
    async def test_create_task_missing_title(self, authenticated_client: AsyncClient, test_project):
        """测试创建任务失败 - 缺少标题"""
        task_data = {
            "description": "Missing title",
            "status": "todo",
            "project_id": test_project.id
        }
        
        response = await authenticated_client.post(
            "/api/v1/tasks",
            json=task_data
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_task_project_not_found(self, authenticated_client: AsyncClient):
        """测试创建任务失败 - 项目不存在"""
        task_data = {
            "title": "Task",
            "status": "todo",
            "project_id": 99999
        }
        
        response = await authenticated_client.post(
            "/api/v1/tasks",
            json=task_data
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_task_success(self, authenticated_client: AsyncClient, db_session, test_user, test_project):
        """测试更新任务成功"""
        from app.models import Task
        task = Task(
            title="Original Title",
            description="Original Description",
            status=TaskStatus.TODO,
            project_id=test_project.id,
            created_by=test_user.id
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        update_data = {
            "title": "Updated Title",
            "status": "in_progress",
            "priority": "high"
        }
        
        response = await authenticated_client.put(
            f"/api/v1/tasks/{task.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == "in_progress"
        assert data["priority"] == "high"

    @pytest.mark.asyncio
    async def test_update_task_mark_done(self, authenticated_client: AsyncClient, db_session, test_user, test_project):
        """测试标记任务为完成"""
        from app.models import Task
        task = Task(
            title="Task to complete",
            status=TaskStatus.TODO,
            project_id=test_project.id,
            created_by=test_user.id
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        update_data = {"status": "done"}
        
        response = await authenticated_client.put(
            f"/api/v1/tasks/{task.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"
        assert data["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_update_task_not_found(self, authenticated_client: AsyncClient):
        """测试更新任务失败 - 任务不存在"""
        update_data = {"title": "Not Found"}
        
        response = await authenticated_client.put(
            "/api/v1/tasks/99999",
            json=update_data
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_task_success(self, authenticated_client: AsyncClient, db_session, test_user, test_project):
        """测试删除任务成功"""
        from app.models import Task
        task = Task(
            title="Task to delete",
            status=TaskStatus.TODO,
            project_id=test_project.id,
            created_by=test_user.id
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        response = await authenticated_client.delete(f"/api/v1/tasks/{task.id}")
        
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, authenticated_client: AsyncClient):
        """测试删除任务失败 - 任务不存在"""
        response = await authenticated_client.delete("/api/v1/tasks/99999")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_add_task_dependency(self, authenticated_client: AsyncClient, db_session, test_user, test_project):
        """测试添加任务依赖成功"""
        from app.models import Task
        task1 = Task(
            title="Task 1",
            project_id=test_project.id,
            created_by=test_user.id
        )
        task2 = Task(
            title="Task 2",
            project_id=test_project.id,
            created_by=test_user.id
        )
        db_session.add_all([task1, task2])
        db_session.commit()
        db_session.refresh(task1)
        db_session.refresh(task2)
        
        dependency_data = {
            "depends_on_task_id": task1.id,
            "dependency_type": "finish_to_start"
        }
        
        response = await authenticated_client.post(
            f"/api/v1/tasks/{task2.id}/dependencies",
            json=dependency_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["depends_on_task_id"] == task1.id

    @pytest.mark.asyncio
    async def test_remove_task_dependency(self, authenticated_client: AsyncClient, db_session, test_user, test_project):
        """测试移除任务依赖成功"""
        from app.models import Task, TaskDependency
        task1 = Task(
            title="Task 1",
            project_id=test_project.id,
            created_by=test_user.id
        )
        task2 = Task(
            title="Task 2",
            project_id=test_project.id,
            created_by=test_user.id
        )
        db_session.add_all([task1, task2])
        db_session.commit()
        db_session.refresh(task1)
        db_session.refresh(task2)
        
        dependency = TaskDependency(
            task_id=task2.id,
            depends_on_task_id=task1.id
        )
        db_session.add(dependency)
        db_session.commit()
        db_session.refresh(dependency)
        
        response = await authenticated_client.delete(
            f"/api/v1/tasks/{task2.id}/dependencies/{dependency.id}"
        )
        
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_add_task_circular_dependency(self, authenticated_client: AsyncClient, db_session, test_user, test_project):
        """测试添加循环依赖"""
        from app.models import Task
        task = Task(
            title="Task",
            project_id=test_project.id,
            created_by=test_user.id
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        dependency_data = {
            "depends_on_task_id": task.id
        }
        
        response = await authenticated_client.post(
            f"/api/v1/tasks/{task.id}/dependencies",
            json=dependency_data
        )
        
        assert response.status_code == 400
