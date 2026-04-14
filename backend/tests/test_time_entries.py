import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models import User, Task, TimeEntry, Project, UserRole


class TestTimeEntries:
    """工时记录接口测试"""

    async def test_list_time_entries_success(
        self,
        client: AsyncClient,
        test_user: User,
        test_task: Task,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试获取工时记录列表成功"""
        entry1 = TimeEntry(
            task_id=test_task.id,
            user_id=test_user.id,
            description="Work on feature",
            hours=4,
            date=datetime.utcnow().date()
        )
        entry2 = TimeEntry(
            task_id=test_task.id,
            user_id=test_user.id,
            description="Code review",
            hours=2,
            date=datetime.utcnow().date() - timedelta(days=1)
        )
        db_session.add_all([entry1, entry2])
        db_session.commit()

        response = await client.get("/api/v1/time-entries", headers=user_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    async def test_list_time_entries_with_filters(
        self,
        client: AsyncClient,
        test_user: User,
        test_task: Task,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试带过滤参数获取工时记录列表"""
        today = datetime.utcnow().date()
        entry = TimeEntry(
            task_id=test_task.id,
            user_id=test_user.id,
            description="Filtered work",
            hours=3,
            date=today
        )
        db_session.add(entry)
        db_session.commit()

        params = {
            "task_id": test_task.id,
            "start_date": today.isoformat(),
            "end_date": today.isoformat(),
            "skip": 0,
            "limit": 10
        }
        response = await client.get("/api/v1/time-entries", headers=user_auth_headers, params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(d["task_id"] == test_task.id for d in data)

    async def test_list_time_entries_member_only_see_own(
        self,
        client: AsyncClient,
        test_user: User,
        test_task: Task,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试普通成员只能看到自己的工时记录"""
        other_user = User(
            email="other@example.com",
            username="other",
            hashed_password="hashed",
            first_name="Other",
            last_name="User",
            role=UserRole.MEMBER
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        own_entry = TimeEntry(
            task_id=test_task.id,
            user_id=test_user.id,
            description="My work",
            hours=4,
            date=datetime.utcnow().date()
        )
        other_entry = TimeEntry(
            task_id=test_task.id,
            user_id=other_user.id,
            description="Someone else's work",
            hours=8,
            date=datetime.utcnow().date()
        )
        db_session.add_all([own_entry, other_entry])
        db_session.commit()

        response = await client.get("/api/v1/time-entries", headers=user_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(d["user_id"] == test_user.id for d in data)

    async def test_list_time_entries_no_auth(self, client: AsyncClient):
        """测试未认证获取工时记录"""
        response = await client.get("/api/v1/time-entries")
        
        assert response.status_code in [401, 403]
        data = response.json()
        assert "detail" in data

    async def test_get_time_summary_success(
        self,
        client: AsyncClient,
        test_user: User,
        test_task: Task,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试获取工时汇总成功"""
        entry1 = TimeEntry(
            task_id=test_task.id,
            user_id=test_user.id,
            description="Work 1",
            hours=4,
            date=datetime.utcnow().date()
        )
        entry2 = TimeEntry(
            task_id=test_task.id,
            user_id=test_user.id,
            description="Work 2",
            hours=2,
            date=datetime.utcnow().date() - timedelta(days=1)
        )
        db_session.add_all([entry1, entry2])
        db_session.commit()

        response = await client.get("/api/v1/time-entries/summary", headers=user_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_hours" in data
        assert "daily_breakdown" in data
        assert isinstance(data["total_hours"], (int, float))
        assert data["total_hours"] >= 6

    async def test_get_time_entry_success(
        self,
        client: AsyncClient,
        test_user: User,
        test_task: Task,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试获取工时记录详情成功"""
        entry = TimeEntry(
            task_id=test_task.id,
            user_id=test_user.id,
            description="Test work",
            hours=5,
            date=datetime.utcnow().date()
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = await client.get(f"/api/v1/time-entries/{entry.id}", headers=user_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == entry.id
        assert data["hours"] == 5
        assert data["description"] == "Test work"

    async def test_get_time_entry_not_found(
        self,
        client: AsyncClient,
        user_auth_headers: dict
    ):
        """测试获取不存在的工时记录"""
        response = await client.get("/api/v1/time-entries/9999", headers=user_auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Time entry not found"

    async def test_get_time_entry_no_permission(
        self,
        client: AsyncClient,
        test_task: Task,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试获取无权限的工时记录"""
        other_user = User(
            email="worker@example.com",
            username="worker",
            hashed_password="hashed",
            first_name="Worker",
            last_name="User",
            role=UserRole.MEMBER
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        entry = TimeEntry(
            task_id=test_task.id,
            user_id=other_user.id,
            description="Private work",
            hours=8,
            date=datetime.utcnow().date()
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = await client.get(f"/api/v1/time-entries/{entry.id}", headers=user_auth_headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Not enough permissions"

    async def test_create_time_entry_success(
        self,
        client: AsyncClient,
        test_user: User,
        test_task: Task,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试创建工时记录成功"""
        entry_data = {
            "task_id": test_task.id,
            "description": "Worked on implementation",
            "hours": 6,
            "date": datetime.utcnow().date().isoformat()
        }
        response = await client.post("/api/v1/time-entries", json=entry_data, headers=user_auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["task_id"] == test_task.id
        assert data["user_id"] == test_user.id
        assert data["hours"] == 6
        assert data["description"] == "Worked on implementation"

        db_session.refresh(test_task)
        assert test_task.actual_hours >= 6

    async def test_create_time_entry_task_not_found(
        self,
        client: AsyncClient,
        user_auth_headers: dict
    ):
        """测试创建工时记录到不存在的任务"""
        entry_data = {
            "task_id": 9999,
            "description": "Test",
            "hours": 4,
            "date": datetime.utcnow().date().isoformat()
        }
        response = await client.post("/api/v1/time-entries", json=entry_data, headers=user_auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Task not found"

    async def test_create_time_entry_no_permission(
        self,
        client: AsyncClient,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试创建工时记录到无权限任务"""
        other_user = User(
            email="owner@example.com",
            username="owner",
            hashed_password="hashed",
            first_name="Owner",
            last_name="User",
            role=UserRole.MEMBER
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        other_project = Project(
            name="Other Project",
            description="Other",
            owner_id=other_user.id
        )
        db_session.add(other_project)
        db_session.commit()
        db_session.refresh(other_project)

        private_task = Task(
            title="Private Task",
            description="Private",
            status="todo",
            priority="medium",
            project_id=other_project.id,
            assignee_id=other_user.id,
            created_by=other_user.id
        )
        db_session.add(private_task)
        db_session.commit()
        db_session.refresh(private_task)

        entry_data = {
            "task_id": private_task.id,
            "description": "Test",
            "hours": 4,
            "date": datetime.utcnow().date().isoformat()
        }
        response = await client.post("/api/v1/time-entries", json=entry_data, headers=user_auth_headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Not enough permissions"

    async def test_create_time_entry_no_auth(self, client: AsyncClient, test_task: Task):
        """测试未认证创建工时记录"""
        entry_data = {
            "task_id": test_task.id,
            "description": "Test",
            "hours": 4,
            "date": datetime.utcnow().date().isoformat()
        }
        response = await client.post("/api/v1/time-entries", json=entry_data)
        
        assert response.status_code in [401, 403]
        data = response.json()
        assert "detail" in data

    async def test_update_time_entry_success(
        self,
        client: AsyncClient,
        test_user: User,
        test_task: Task,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试更新工时记录成功"""
        entry = TimeEntry(
            task_id=test_task.id,
            user_id=test_user.id,
            description="Original work",
            hours=4,
            date=datetime.utcnow().date()
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        original_hours = test_task.actual_hours or 0

        update_data = {
            "description": "Updated work",
            "hours": 6
        }
        response = await client.put(f"/api/v1/time-entries/{entry.id}", json=update_data, headers=user_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated work"
        assert data["hours"] == 6

        db_session.refresh(test_task)
        assert test_task.actual_hours == original_hours + 2

    async def test_update_time_entry_not_found(
        self,
        client: AsyncClient,
        user_auth_headers: dict
    ):
        """测试更新不存在的工时记录"""
        update_data = {"hours": 5}
        response = await client.put("/api/v1/time-entries/9999", json=update_data, headers=user_auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Time entry not found"

    async def test_update_time_entry_no_permission(
        self,
        client: AsyncClient,
        test_task: Task,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试更新无权限的工时记录"""
        other_user = User(
            email="worker2@example.com",
            username="worker2",
            hashed_password="hashed",
            first_name="Worker",
            last_name="User",
            role=UserRole.MEMBER
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        entry = TimeEntry(
            task_id=test_task.id,
            user_id=other_user.id,
            description="Not mine",
            hours=8,
            date=datetime.utcnow().date()
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        update_data = {"hours": 5}
        response = await client.put(f"/api/v1/time-entries/{entry.id}", json=update_data, headers=user_auth_headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Not enough permissions"

    async def test_delete_time_entry_success(
        self,
        client: AsyncClient,
        test_user: User,
        test_task: Task,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试删除工时记录成功"""
        entry = TimeEntry(
            task_id=test_task.id,
            user_id=test_user.id,
            description="To be deleted",
            hours=3,
            date=datetime.utcnow().date()
        )
        db_session.add(entry)
        test_task.actual_hours = (test_task.actual_hours or 0) + 3
        db_session.commit()
        db_session.refresh(entry)
        db_session.refresh(test_task)

        original_hours = test_task.actual_hours or 0

        response = await client.delete(f"/api/v1/time-entries/{entry.id}", headers=user_auth_headers)
        
        assert response.status_code == 204
        
        db_session.refresh(test_task)
        assert test_task.actual_hours == max(0, original_hours - 3)
        
        deleted_entry = db_session.query(TimeEntry).filter(TimeEntry.id == entry.id).first()
        assert deleted_entry is None

    async def test_delete_time_entry_not_found(
        self,
        client: AsyncClient,
        user_auth_headers: dict
    ):
        """测试删除不存在的工时记录"""
        response = await client.delete("/api/v1/time-entries/9999", headers=user_auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Time entry not found"

    async def test_delete_time_entry_no_permission(
        self,
        client: AsyncClient,
        test_task: Task,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试删除无权限的工时记录"""
        other_user = User(
            email="worker3@example.com",
            username="worker3",
            hashed_password="hashed",
            first_name="Worker",
            last_name="User",
            role=UserRole.MEMBER
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        entry = TimeEntry(
            task_id=test_task.id,
            user_id=other_user.id,
            description="Not mine to delete",
            hours=5,
            date=datetime.utcnow().date()
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = await client.delete(f"/api/v1/time-entries/{entry.id}", headers=user_auth_headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Not enough permissions"

    async def test_delete_time_entry_no_auth(
        self,
        client: AsyncClient,
        test_user: User,
        test_task: Task,
        db_session: Session
    ):
        """测试未认证删除工时记录"""
        entry = TimeEntry(
            task_id=test_task.id,
            user_id=test_user.id,
            description="Test",
            hours=4,
            date=datetime.utcnow().date()
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        response = await client.delete(f"/api/v1/time-entries/{entry.id}")
        
        assert response.status_code in [401, 403]
        data = response.json()
        assert "detail" in data
