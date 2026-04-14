import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import User, UserRole, Project, ProjectStatus, Task, TaskStatus, TaskPriority, TimeEntry


class TestListTimeEntries:
    def test_list_time_entries_as_admin(self, client: TestClient, admin_auth_headers: dict, test_time_entry: TimeEntry):
        response = client.get("/api/v1/time-entries", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_time_entries_as_member_only_own(self, client: TestClient, auth_headers: dict, test_time_entry: TimeEntry, test_user: User):
        response = client.get("/api/v1/time-entries", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        for entry in data:
            assert entry["user_id"] == test_user.id

    def test_list_time_entries_with_task_filter(self, client: TestClient, auth_headers: dict, test_time_entry: TimeEntry, test_task: Task):
        response = client.get(
            "/api/v1/time-entries",
            params={"task_id": test_task.id},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for entry in data:
            assert entry["task_id"] == test_task.id

    def test_list_time_entries_with_user_filter(self, client: TestClient, admin_auth_headers: dict, test_time_entry: TimeEntry, test_user: User):
        response = client.get(
            "/api/v1/time-entries",
            params={"user_id": test_user.id},
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for entry in data:
            assert entry["user_id"] == test_user.id

    def test_list_time_entries_with_date_range(self, client: TestClient, auth_headers: dict, test_time_entry: TimeEntry):
        start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
        end_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
        
        response = client.get(
            "/api/v1/time-entries",
            params={"start_date": start_date, "end_date": end_date},
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_list_time_entries_pagination(self, client: TestClient, auth_headers: dict, db: Session, test_task: Task, test_user: User):
        for i in range(5):
            entry = TimeEntry(
                task_id=test_task.id,
                user_id=test_user.id,
                hours=1.0,
                date=datetime.utcnow(),
            )
            db.add(entry)
        db.commit()

        response = client.get(
            "/api/v1/time-entries",
            params={"skip": 0, "limit": 2},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_time_entries_unauthorized(self, client: TestClient):
        response = client.get("/api/v1/time-entries")
        assert response.status_code == 403


class TestGetTimeEntry:
    def test_get_time_entry_success(self, client: TestClient, auth_headers: dict, test_time_entry: TimeEntry):
        response = client.get(f"/api/v1/time-entries/{test_time_entry.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_time_entry.id
        assert data["hours"] == test_time_entry.hours

    def test_get_time_entry_not_found(self, client: TestClient, admin_auth_headers: dict):
        response = client.get("/api/v1/time-entries/9999", headers=admin_auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_time_entry_unauthorized(self, client: TestClient, test_time_entry: TimeEntry):
        response = client.get(f"/api/v1/time-entries/{test_time_entry.id}")
        assert response.status_code == 403

    def test_get_time_entry_other_user_denied(self, client: TestClient, db: Session, test_time_entry: TimeEntry):
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed",
            first_name="Other",
            last_name="User",
            role=UserRole.MEMBER,
            is_active=True,
        )
        db.add(other_user)
        db.commit()
        
        from app.auth import create_access_token
        token = create_access_token(subject=other_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(f"/api/v1/time-entries/{test_time_entry.id}", headers=headers)
        assert response.status_code == 403


class TestCreateTimeEntry:
    def test_create_time_entry_success(self, client: TestClient, auth_headers: dict, test_task: Task):
        response = client.post(
            "/api/v1/time-entries",
            json={
                "task_id": test_task.id,
                "description": "Work on task",
                "hours": 2.5,
                "date": datetime.utcnow().strftime("%Y-%m-%d")
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["hours"] == 2.5
        assert data["description"] == "Work on task"

    def test_create_time_entry_updates_task_hours(self, client: TestClient, auth_headers: dict, test_task: Task, db: Session):
        initial_hours = test_task.actual_hours or 0
        
        response = client.post(
            "/api/v1/time-entries",
            json={
                "task_id": test_task.id,
                "hours": 3.0,
                "date": datetime.utcnow().strftime("%Y-%m-%d")
            },
            headers=auth_headers
        )
        assert response.status_code == 201

        db.refresh(test_task)
        assert test_task.actual_hours == initial_hours + 3.0

    def test_create_time_entry_task_not_found(self, client: TestClient, auth_headers: dict):
        response = client.post(
            "/api/v1/time-entries",
            json={
                "task_id": 9999,
                "hours": 1.0,
                "date": datetime.utcnow().strftime("%Y-%m-%d")
            },
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_create_time_entry_non_member_denied(self, client: TestClient, db: Session, test_task: Task):
        other_user = User(
            email="nonmember@example.com",
            username="nonmember",
            hashed_password="hashed",
            first_name="Non",
            last_name="Member",
            role=UserRole.MEMBER,
            is_active=True,
        )
        db.add(other_user)
        db.commit()
        
        from app.auth import create_access_token
        token = create_access_token(subject=other_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/api/v1/time-entries",
            json={
                "task_id": test_task.id,
                "hours": 1.0,
                "date": datetime.utcnow().strftime("%Y-%m-%d")
            },
            headers=headers
        )
        assert response.status_code == 403

    def test_create_time_entry_unauthorized(self, client: TestClient, test_task: Task):
        response = client.post(
            "/api/v1/time-entries",
            json={
                "task_id": test_task.id,
                "hours": 1.0,
                "date": datetime.utcnow().strftime("%Y-%m-%d")
            }
        )
        assert response.status_code == 403

    def test_create_time_entry_zero_hours(self, client: TestClient, auth_headers: dict, test_task: Task):
        response = client.post(
            "/api/v1/time-entries",
            json={
                "task_id": test_task.id,
                "hours": 0,
                "date": datetime.utcnow().strftime("%Y-%m-%d")
            },
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_time_entry_negative_hours(self, client: TestClient, auth_headers: dict, test_task: Task):
        response = client.post(
            "/api/v1/time-entries",
            json={
                "task_id": test_task.id,
                "hours": -1.0,
                "date": datetime.utcnow().strftime("%Y-%m-%d")
            },
            headers=auth_headers
        )
        assert response.status_code == 422


class TestUpdateTimeEntry:
    def test_update_time_entry_hours(self, client: TestClient, auth_headers: dict, test_time_entry: TimeEntry, db: Session):
        initial_task_hours = test_time_entry.task.actual_hours
        initial_entry_hours = test_time_entry.hours
        
        response = client.put(
            f"/api/v1/time-entries/{test_time_entry.id}",
            json={"hours": 5.0},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["hours"] == 5.0

        db.refresh(test_time_entry.task)
        expected_task_hours = initial_task_hours - initial_entry_hours + 5.0
        assert test_time_entry.task.actual_hours == expected_task_hours

    def test_update_time_entry_description(self, client: TestClient, auth_headers: dict, test_time_entry: TimeEntry):
        response = client.put(
            f"/api/v1/time-entries/{test_time_entry.id}",
            json={"description": "Updated description"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"

    def test_update_time_entry_not_found(self, client: TestClient, admin_auth_headers: dict):
        response = client.put(
            "/api/v1/time-entries/9999",
            json={"hours": 1.0},
            headers=admin_auth_headers
        )
        assert response.status_code == 404

    def test_update_time_entry_other_user_denied(self, client: TestClient, db: Session, test_time_entry: TimeEntry):
        other_user = User(
            email="other2@example.com",
            username="otheruser2",
            hashed_password="hashed",
            first_name="Other",
            last_name="User2",
            role=UserRole.MEMBER,
            is_active=True,
        )
        db.add(other_user)
        db.commit()
        
        from app.auth import create_access_token
        token = create_access_token(subject=other_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.put(
            f"/api/v1/time-entries/{test_time_entry.id}",
            json={"hours": 1.0},
            headers=headers
        )
        assert response.status_code == 403


class TestDeleteTimeEntry:
    def test_delete_time_entry_success(self, client: TestClient, auth_headers: dict, test_time_entry: TimeEntry, db: Session):
        entry_id = test_time_entry.id
        task_hours_before = test_time_entry.task.actual_hours
        entry_hours = test_time_entry.hours

        response = client.delete(f"/api/v1/time-entries/{entry_id}", headers=auth_headers)
        assert response.status_code == 204

        response = client.get(f"/api/v1/time-entries/{entry_id}", headers=auth_headers)
        assert response.status_code == 404

        db.refresh(test_time_entry.task)
        assert test_time_entry.task.actual_hours == task_hours_before - entry_hours

    def test_delete_time_entry_not_found(self, client: TestClient, admin_auth_headers: dict):
        response = client.delete("/api/v1/time-entries/9999", headers=admin_auth_headers)
        assert response.status_code == 404

    def test_delete_time_entry_other_user_denied(self, client: TestClient, db: Session, test_time_entry: TimeEntry):
        other_user = User(
            email="other3@example.com",
            username="otheruser3",
            hashed_password="hashed",
            first_name="Other",
            last_name="User3",
            role=UserRole.MEMBER,
            is_active=True,
        )
        db.add(other_user)
        db.commit()
        
        from app.auth import create_access_token
        token = create_access_token(subject=other_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.delete(f"/api/v1/time-entries/{test_time_entry.id}", headers=headers)
        assert response.status_code == 403


class TestTimeSummary:
    def test_get_time_summary_success(self, client: TestClient, auth_headers: dict, test_time_entry: TimeEntry):
        response = client.get("/api/v1/time-entries/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_hours" in data
        assert "daily_breakdown" in data

    def test_get_time_summary_with_project_filter(self, client: TestClient, auth_headers: dict, test_time_entry: TimeEntry, test_project: Project):
        response = client.get(
            "/api/v1/time-entries/summary",
            params={"project_id": test_project.id},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_hours" in data

    def test_get_time_summary_with_user_filter(self, client: TestClient, admin_auth_headers: dict, test_time_entry: TimeEntry, test_user: User):
        response = client.get(
            "/api/v1/time-entries/summary",
            params={"user_id": test_user.id},
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_hours" in data

    def test_get_time_summary_member_only_own(self, client: TestClient, auth_headers: dict, test_time_entry: TimeEntry):
        response = client.get(
            "/api/v1/time-entries/summary",
            params={"user_id": 9999},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_hours"] >= 0

    def test_get_time_summary_unauthorized(self, client: TestClient):
        response = client.get("/api/v1/time-entries/summary")
        assert response.status_code == 403
