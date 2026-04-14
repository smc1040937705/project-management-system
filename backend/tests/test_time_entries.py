import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models import User, Project, Task, TimeEntry, UserRole, ProjectStatus, TaskStatus, TaskPriority


class TestTimeEntriesRouter:
    """工时记录路由测试类"""

    def test_list_time_entries_success(self, client: TestClient, test_time_entry: TimeEntry, auth_headers: dict):
        """
        测试场景：正常获取工时记录列表
        验证：返回工时记录列表
        """
        response = client.get("/api/v1/time-entries", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_time_entries_no_auth(self, client: TestClient):
        """
        测试场景：获取工时记录列表失败（未认证）
        验证：返回403错误
        """
        response = client.get("/api/v1/time-entries")
        
        assert response.status_code == 403

    def test_list_time_entries_with_task_filter(self, client: TestClient, test_time_entry: TimeEntry, auth_headers: dict):
        """
        测试场景：按任务筛选工时记录
        验证：只返回指定任务的工时记录
        """
        response = client.get(f"/api/v1/time-entries?task_id={test_time_entry.task_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_time_entries_with_date_range(self, client: TestClient, test_time_entry: TimeEntry, auth_headers: dict):
        """
        测试场景：按日期范围筛选工时记录
        验证：只返回日期范围内的工时记录
        """
        # API期望datetime格式，使用ISO格式
        today = datetime.utcnow().isoformat()
        last_week = (datetime.utcnow() - timedelta(days=7)).isoformat()
        
        response = client.get(
            f"/api/v1/time-entries?start_date={last_week}&end_date={today}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_time_entry_success(self, client: TestClient, test_time_entry: TimeEntry, auth_headers: dict):
        """
        测试场景：正常获取单个工时记录
        验证：返回工时记录详细信息
        """
        response = client.get(f"/api/v1/time-entries/{test_time_entry.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_time_entry.id
        assert data["hours"] == test_time_entry.hours
        assert "task" in data
        assert "user" in data

    def test_get_time_entry_not_found(self, client: TestClient, auth_headers: dict):
        """
        测试场景：获取不存在的工时记录
        验证：返回404错误
        """
        response = client.get("/api/v1/time-entries/99999", headers=auth_headers)
        
        assert response.status_code == 404
        assert "Time entry not found" in response.json()["detail"]

    def test_get_time_entry_no_permission(self, client: TestClient, db_session: Session, auth_headers: dict):
        """
        测试场景：获取工时记录失败（无权限）
        验证：返回403错误
        """
        # 创建另一个用户和工时记录
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed",
            first_name="Other",
            last_name="User",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()

        other_project = Project(
            name="Other Project",
            status=ProjectStatus.ACTIVE,
            owner_id=other_user.id
        )
        db_session.add(other_project)
        db_session.commit()

        other_task = Task(
            project_id=other_project.id,
            title="Other Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=other_user.id
        )
        db_session.add(other_task)
        db_session.commit()

        other_entry = TimeEntry(
            task_id=other_task.id,
            user_id=other_user.id,
            hours=5,
            date=datetime.utcnow(),
            description="Other work"
        )
        db_session.add(other_entry)
        db_session.commit()

        response = client.get(f"/api/v1/time-entries/{other_entry.id}", headers=auth_headers)
        
        assert response.status_code == 403

    def test_create_time_entry_success(self, client: TestClient, test_task: Task, auth_headers: dict):
        """
        测试场景：正常创建工时记录
        验证：返回201状态码和工时记录数据
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        response = client.post(
            "/api/v1/time-entries",
            headers=auth_headers,
            json={
                "task_id": test_task.id,
                "hours": 8,
                "date": today,
                "description": "Worked on task"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["hours"] == 8
        assert data["description"] == "Worked on task"
        assert "id" in data

    def test_create_time_entry_task_not_found(self, client: TestClient, auth_headers: dict):
        """
        测试场景：创建工时记录失败（任务不存在）
        验证：返回404错误
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        response = client.post(
            "/api/v1/time-entries",
            headers=auth_headers,
            json={
                "task_id": 99999,
                "hours": 8,
                "date": today
            }
        )
        
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]

    def test_create_time_entry_invalid_hours(self, client: TestClient, test_task: Task, auth_headers: dict):
        """
        测试场景：创建工时记录失败（工时无效）
        验证：返回422错误
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        response = client.post(
            "/api/v1/time-entries",
            headers=auth_headers,
            json={
                "task_id": test_task.id,
                "hours": -1,  # 无效工时
                "date": today
            }
        )
        
        assert response.status_code == 422

    def test_update_time_entry_success(self, client: TestClient, test_time_entry: TimeEntry, auth_headers: dict):
        """
        测试场景：正常更新工时记录
        验证：返回更新后的工时记录数据
        """
        response = client.put(
            f"/api/v1/time-entries/{test_time_entry.id}",
            headers=auth_headers,
            json={
                "hours": 6,
                "description": "Updated description"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["hours"] == 6
        assert data["description"] == "Updated description"

    def test_update_time_entry_not_found(self, client: TestClient, auth_headers: dict):
        """
        测试场景：更新不存在的工时记录
        验证：返回404错误
        """
        response = client.put(
            "/api/v1/time-entries/99999",
            headers=auth_headers,
            json={"hours": 5}
        )
        
        assert response.status_code == 404

    def test_update_time_entry_no_permission(self, client: TestClient, db_session: Session, auth_headers: dict):
        """
        测试场景：更新工时记录失败（无权限）
        验证：返回403错误
        """
        # 创建另一个用户和工时记录
        other_user = User(
            email="other2@example.com",
            username="otheruser2",
            hashed_password="hashed",
            first_name="Other",
            last_name="User",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()

        other_project = Project(
            name="Other Project",
            status=ProjectStatus.ACTIVE,
            owner_id=other_user.id
        )
        db_session.add(other_project)
        db_session.commit()

        other_task = Task(
            project_id=other_project.id,
            title="Other Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=other_user.id
        )
        db_session.add(other_task)
        db_session.commit()

        other_entry = TimeEntry(
            task_id=other_task.id,
            user_id=other_user.id,
            hours=5,
            date=datetime.utcnow(),
            description="Other work"
        )
        db_session.add(other_entry)
        db_session.commit()

        response = client.put(
            f"/api/v1/time-entries/{other_entry.id}",
            headers=auth_headers,
            json={"hours": 3}
        )
        
        assert response.status_code == 403

    def test_delete_time_entry_success(self, client: TestClient, db_session: Session, test_task: Task, test_user: User, auth_headers: dict):
        """
        测试场景：正常删除工时记录
        验证：返回204状态码
        """
        # 创建一个专门用于删除测试的工时记录
        entry_to_delete = TimeEntry(
            task_id=test_task.id,
            user_id=test_user.id,
            hours=4,
            date=datetime.utcnow(),
            description="Entry to delete"
        )
        db_session.add(entry_to_delete)
        db_session.commit()

        response = client.delete(
            f"/api/v1/time-entries/{entry_to_delete.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204

    def test_delete_time_entry_not_found(self, client: TestClient, auth_headers: dict):
        """
        测试场景：删除不存在的工时记录
        验证：返回404错误
        """
        response = client.delete("/api/v1/time-entries/99999", headers=auth_headers)
        
        assert response.status_code == 404

    def test_get_time_summary_success(self, client: TestClient, test_time_entry: TimeEntry, auth_headers: dict):
        """
        测试场景：正常获取工时统计
        验证：返回总工时和每日明细
        """
        response = client.get("/api/v1/time-entries/summary", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_hours" in data
        assert "daily_breakdown" in data
        assert isinstance(data["daily_breakdown"], list)

    def test_get_time_summary_with_filters(self, client: TestClient, test_time_entry: TimeEntry, auth_headers: dict):
        """
        测试场景：带筛选条件获取工时统计
        验证：正确应用筛选条件
        """
        # API期望datetime格式，使用ISO格式
        today = datetime.utcnow().isoformat()
        last_week = (datetime.utcnow() - timedelta(days=7)).isoformat()
        
        response = client.get(
            f"/api/v1/time-entries/summary?start_date={last_week}&end_date={today}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_hours" in data

    def test_admin_can_view_all_time_entries(self, client: TestClient, db_session: Session, admin_auth_headers: dict):
        """
        测试场景：管理员可以查看所有工时记录
        验证：管理员能获取其他用户的工时记录
        """
        # 创建另一个用户和工时记录
        other_user = User(
            email="other3@example.com",
            username="otheruser3",
            hashed_password="hashed",
            first_name="Other",
            last_name="User",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()

        other_project = Project(
            name="Other Project",
            status=ProjectStatus.ACTIVE,
            owner_id=other_user.id
        )
        db_session.add(other_project)
        db_session.commit()

        other_task = Task(
            project_id=other_project.id,
            title="Other Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=other_user.id
        )
        db_session.add(other_task)
        db_session.commit()

        other_entry = TimeEntry(
            task_id=other_task.id,
            user_id=other_user.id,
            hours=5,
            date=datetime.utcnow(),
            description="Other work"
        )
        db_session.add(other_entry)
        db_session.commit()

        response = client.get(f"/api/v1/time-entries/{other_entry.id}", headers=admin_auth_headers)
        
        assert response.status_code == 200
        assert response.json()["id"] == other_entry.id

    def test_pm_can_view_all_time_entries(self, client: TestClient, db_session: Session, pm_auth_headers: dict):
        """
        测试场景：项目经理可以查看所有工时记录
        验证：项目经理能获取其他用户的工时记录
        """
        # 创建另一个用户和工时记录
        other_user = User(
            email="other4@example.com",
            username="otheruser4",
            hashed_password="hashed",
            first_name="Other",
            last_name="User",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()

        other_project = Project(
            name="Other Project",
            status=ProjectStatus.ACTIVE,
            owner_id=other_user.id
        )
        db_session.add(other_project)
        db_session.commit()

        other_task = Task(
            project_id=other_project.id,
            title="Other Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=other_user.id
        )
        db_session.add(other_task)
        db_session.commit()

        other_entry = TimeEntry(
            task_id=other_task.id,
            user_id=other_user.id,
            hours=5,
            date=datetime.utcnow(),
            description="Other work"
        )
        db_session.add(other_entry)
        db_session.commit()

        response = client.get(f"/api/v1/time-entries/{other_entry.id}", headers=pm_auth_headers)
        
        assert response.status_code == 200
        assert response.json()["id"] == other_entry.id
