import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import User, UserRole, Project, ProjectStatus, Task, TaskStatus, TaskPriority, TaskDependency


class TestListTasks:
    def test_list_tasks_as_admin(self, client: TestClient, admin_auth_headers: dict, test_task: Task):
        response = client.get("/api/v1/tasks", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_tasks_with_project_filter(self, client: TestClient, admin_auth_headers: dict, test_task: Task, test_project: Project):
        response = client.get(
            "/api/v1/tasks",
            params={"project_id": test_project.id},
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for task in data:
            assert task["project_id"] == test_project.id

    def test_list_tasks_with_status_filter(self, client: TestClient, admin_auth_headers: dict, test_task: Task):
        response = client.get(
            "/api/v1/tasks",
            params={"status": "todo"},
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for task in data:
            assert task["status"] == "todo"

    def test_list_tasks_with_priority_filter(self, client: TestClient, admin_auth_headers: dict, test_task: Task):
        response = client.get(
            "/api/v1/tasks",
            params={"priority": "medium"},
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for task in data:
            assert task["priority"] == "medium"

    def test_list_tasks_with_assignee_filter(self, client: TestClient, admin_auth_headers: dict, db: Session, test_project: Project, test_user: User):
        task = Task(
            project_id=test_project.id,
            title="Assigned Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=test_user.id,
            assignee_id=test_user.id,
        )
        db.add(task)
        db.commit()

        response = client.get(
            "/api/v1/tasks",
            params={"assignee_id": test_user.id},
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for t in data:
            assert t["assignee_id"] == test_user.id

    def test_list_tasks_with_search(self, client: TestClient, admin_auth_headers: dict, test_task: Task):
        response = client.get(
            "/api/v1/tasks",
            params={"search": "Test"},
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for task in data:
            assert "Test" in task["title"] or "Test" in (task.get("description") or "")

    def test_list_tasks_pagination(self, client: TestClient, admin_auth_headers: dict, db: Session, test_project: Project, test_user: User):
        for i in range(5):
            task = Task(
                project_id=test_project.id,
                title=f"Task {i}",
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                created_by=test_user.id,
            )
            db.add(task)
        db.commit()

        response = client.get(
            "/api/v1/tasks",
            params={"skip": 0, "limit": 2},
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_tasks_unauthorized(self, client: TestClient):
        response = client.get("/api/v1/tasks")
        assert response.status_code == 403


class TestGetTask:
    def test_get_task_success(self, client: TestClient, auth_headers: dict, test_task: Task):
        response = client.get(f"/api/v1/tasks/{test_task.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_task.id
        assert data["title"] == test_task.title

    def test_get_task_not_found(self, client: TestClient, admin_auth_headers: dict):
        response = client.get("/api/v1/tasks/9999", headers=admin_auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_task_unauthorized(self, client: TestClient, test_task: Task):
        response = client.get(f"/api/v1/tasks/{test_task.id}")
        assert response.status_code == 403

    def test_get_task_non_member_access_denied(self, client: TestClient, db: Session, test_task: Task):
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

        response = client.get(f"/api/v1/tasks/{test_task.id}", headers=headers)
        assert response.status_code == 403


class TestCreateTask:
    def test_create_task_success(self, client: TestClient, auth_headers: dict, test_project: Project):
        response = client.post(
            "/api/v1/tasks",
            json={
                "project_id": test_project.id,
                "title": "New Task",
                "description": "New task description",
                "status": "todo",
                "priority": "high"
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Task"
        assert data["description"] == "New task description"
        assert data["status"] == "todo"
        assert data["priority"] == "high"

    def test_create_task_with_assignee(self, client: TestClient, auth_headers: dict, test_project: Project, test_user: User):
        response = client.post(
            "/api/v1/tasks",
            json={
                "project_id": test_project.id,
                "title": "Task with Assignee",
                "status": "todo",
                "priority": "medium",
                "assignee_id": test_user.id
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["assignee_id"] == test_user.id

    def test_create_task_with_estimated_hours(self, client: TestClient, auth_headers: dict, test_project: Project):
        response = client.post(
            "/api/v1/tasks",
            json={
                "project_id": test_project.id,
                "title": "Task with Hours",
                "status": "todo",
                "priority": "medium",
                "estimated_hours": 8.5
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["estimated_hours"] == 8.5

    def test_create_task_project_not_found(self, client: TestClient, auth_headers: dict):
        response = client.post(
            "/api/v1/tasks",
            json={
                "project_id": 9999,
                "title": "Invalid Task",
                "status": "todo",
                "priority": "medium"
            },
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_create_task_assignee_not_found(self, client: TestClient, auth_headers: dict, test_project: Project):
        response = client.post(
            "/api/v1/tasks",
            json={
                "project_id": test_project.id,
                "title": "Task with Invalid Assignee",
                "status": "todo",
                "priority": "medium",
                "assignee_id": 9999
            },
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_create_task_unauthorized(self, client: TestClient, test_project: Project):
        response = client.post(
            "/api/v1/tasks",
            json={
                "project_id": test_project.id,
                "title": "Unauthorized Task",
                "status": "todo",
                "priority": "medium"
            }
        )
        assert response.status_code == 403

    def test_create_task_empty_title(self, client: TestClient, auth_headers: dict, test_project: Project):
        response = client.post(
            "/api/v1/tasks",
            json={
                "project_id": test_project.id,
                "title": "",
                "status": "todo",
                "priority": "medium"
            },
            headers=auth_headers
        )
        assert response.status_code == 422


class TestUpdateTask:
    def test_update_task_as_assignee(self, client: TestClient, db: Session, test_project: Project, test_user: User):
        task = Task(
            project_id=test_project.id,
            title="Task to Update",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=test_user.id,
            assignee_id=test_user.id,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        from app.auth import create_access_token
        token = create_access_token(subject=test_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.put(
            f"/api/v1/tasks/{task.id}",
            json={"title": "Updated Task Title"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Task Title"

    def test_update_task_status_to_done(self, client: TestClient, auth_headers: dict, test_task: Task):
        response = client.put(
            f"/api/v1/tasks/{test_task.id}",
            json={"status": "done"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"
        assert data.get("completed_at") is not None

    def test_update_task_priority(self, client: TestClient, auth_headers: dict, test_task: Task):
        response = client.put(
            f"/api/v1/tasks/{test_task.id}",
            json={"priority": "critical"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == "critical"

    def test_update_task_assignee(self, client: TestClient, auth_headers: dict, test_task: Task, db: Session):
        new_assignee = User(
            email="newassignee@example.com",
            username="newassignee",
            hashed_password="hashed",
            first_name="New",
            last_name="Assignee",
            role=UserRole.MEMBER,
            is_active=True,
        )
        db.add(new_assignee)
        db.commit()
        db.refresh(new_assignee)

        response = client.put(
            f"/api/v1/tasks/{test_task.id}",
            json={"assignee_id": new_assignee.id},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["assignee_id"] == new_assignee.id

    def test_update_task_clear_assignee(self, client: TestClient, db: Session, test_project: Project, test_user: User):
        task = Task(
            project_id=test_project.id,
            title="Task with Assignee",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=test_user.id,
            assignee_id=test_user.id,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        from app.auth import create_access_token
        token = create_access_token(subject=test_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.put(
            f"/api/v1/tasks/{task.id}",
            json={"assignee_id": 0},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["assignee_id"] is None or data["assignee_id"] == 0

    def test_update_task_not_found(self, client: TestClient, admin_auth_headers: dict):
        response = client.put(
            "/api/v1/tasks/9999",
            json={"title": "Nonexistent"},
            headers=admin_auth_headers
        )
        assert response.status_code == 404

    def test_update_task_unauthorized(self, client: TestClient, test_task: Task):
        response = client.put(
            f"/api/v1/tasks/{test_task.id}",
            json={"title": "Unauthorized Update"}
        )
        assert response.status_code == 403


class TestDeleteTask:
    def test_delete_task_as_project_owner(self, client: TestClient, auth_headers: dict, test_task: Task):
        response = client.delete(f"/api/v1/tasks/{test_task.id}", headers=auth_headers)
        assert response.status_code == 204

    def test_delete_task_as_admin(self, client: TestClient, admin_auth_headers: dict, db: Session, test_project: Project, test_user: User):
        task = Task(
            project_id=test_project.id,
            title="Task to Delete",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=test_user.id,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        response = client.delete(f"/api/v1/tasks/{task.id}", headers=admin_auth_headers)
        assert response.status_code == 204

    def test_delete_task_not_found(self, client: TestClient, admin_auth_headers: dict):
        response = client.delete("/api/v1/tasks/9999", headers=admin_auth_headers)
        assert response.status_code == 404

    def test_delete_task_unauthorized(self, client: TestClient, test_task: Task):
        response = client.delete(f"/api/v1/tasks/{test_task.id}")
        assert response.status_code == 403

    def test_delete_task_non_owner_denied(self, client: TestClient, db: Session, test_task: Task):
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

        response = client.delete(f"/api/v1/tasks/{test_task.id}", headers=headers)
        assert response.status_code == 403


class TestTaskDependencies:
    def test_add_dependency_success(self, client: TestClient, auth_headers: dict, db: Session, test_project: Project, test_user: User):
        task1 = Task(
            project_id=test_project.id,
            title="Task 1",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=test_user.id,
        )
        task2 = Task(
            project_id=test_project.id,
            title="Task 2",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=test_user.id,
        )
        db.add_all([task1, task2])
        db.commit()
        db.refresh(task1)
        db.refresh(task2)

        response = client.post(
            f"/api/v1/tasks/{task1.id}/dependencies",
            json={"depends_on_task_id": task2.id, "dependency_type": "finish_to_start"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["depends_on_task_id"] == task2.id

    def test_add_dependency_different_projects(self, client: TestClient, auth_headers: dict, db: Session, test_project: Project, test_user: User):
        other_project = Project(
            name="Other Project",
            status=ProjectStatus.ACTIVE,
            owner_id=test_user.id,
        )
        db.add(other_project)
        db.commit()
        db.refresh(other_project)

        task1 = Task(
            project_id=test_project.id,
            title="Task 1",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=test_user.id,
        )
        task2 = Task(
            project_id=other_project.id,
            title="Task 2",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=test_user.id,
        )
        db.add_all([task1, task2])
        db.commit()
        db.refresh(task1)
        db.refresh(task2)

        response = client.post(
            f"/api/v1/tasks/{task1.id}/dependencies",
            json={"depends_on_task_id": task2.id},
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "same project" in response.json()["detail"].lower()

    def test_add_dependency_self_reference(self, client: TestClient, auth_headers: dict, test_task: Task):
        response = client.post(
            f"/api/v1/tasks/{test_task.id}/dependencies",
            json={"depends_on_task_id": test_task.id},
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "itself" in response.json()["detail"].lower()

    def test_add_dependency_duplicate(self, client: TestClient, auth_headers: dict, db: Session, test_project: Project, test_user: User):
        task1 = Task(
            project_id=test_project.id,
            title="Task 1",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=test_user.id,
        )
        task2 = Task(
            project_id=test_project.id,
            title="Task 2",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=test_user.id,
        )
        db.add_all([task1, task2])
        db.commit()
        db.refresh(task1)
        db.refresh(task2)

        dependency = TaskDependency(
            task_id=task1.id,
            depends_on_task_id=task2.id,
            dependency_type="finish_to_start",
        )
        db.add(dependency)
        db.commit()

        response = client.post(
            f"/api/v1/tasks/{task1.id}/dependencies",
            json={"depends_on_task_id": task2.id},
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_remove_dependency_success(self, client: TestClient, auth_headers: dict, db: Session, test_project: Project, test_user: User):
        task1 = Task(
            project_id=test_project.id,
            title="Task 1",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=test_user.id,
        )
        task2 = Task(
            project_id=test_project.id,
            title="Task 2",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=test_user.id,
        )
        db.add_all([task1, task2])
        db.commit()
        db.refresh(task1)
        db.refresh(task2)

        dependency = TaskDependency(
            task_id=task1.id,
            depends_on_task_id=task2.id,
            dependency_type="finish_to_start",
        )
        db.add(dependency)
        db.commit()
        db.refresh(dependency)

        response = client.delete(
            f"/api/v1/tasks/{task1.id}/dependencies/{dependency.id}",
            headers=auth_headers
        )
        assert response.status_code == 204

    def test_remove_dependency_not_found(self, client: TestClient, admin_auth_headers: dict, test_task: Task):
        response = client.delete(
            f"/api/v1/tasks/{test_task.id}/dependencies/9999",
            headers=admin_auth_headers
        )
        assert response.status_code == 404
