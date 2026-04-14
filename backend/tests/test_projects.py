import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import User, UserRole, Project, ProjectStatus, Task, TaskStatus


class TestListProjects:
    def test_list_projects_as_admin(self, client: TestClient, admin_auth_headers: dict, test_project: Project):
        response = client.get("/api/v1/projects", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_projects_as_member(self, client: TestClient, auth_headers: dict, test_project: Project, test_user: User):
        response = client.get("/api/v1/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_projects_with_status_filter(self, client: TestClient, admin_auth_headers: dict, test_project: Project):
        response = client.get(
            "/api/v1/projects",
            params={"status": "active"},
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for project in data:
            assert project["status"] == "active"

    def test_list_projects_with_search(self, client: TestClient, admin_auth_headers: dict, test_project: Project):
        response = client.get(
            "/api/v1/projects",
            params={"search": "Test"},
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for project in data:
            assert "Test" in project["name"] or "Test" in (project.get("description") or "")

    def test_list_projects_pagination(self, client: TestClient, admin_auth_headers: dict, db: Session, admin_user: User):
        for i in range(5):
            project = Project(
                name=f"Project {i}",
                status=ProjectStatus.ACTIVE,
                owner_id=admin_user.id,
            )
            db.add(project)
        db.commit()

        response = client.get(
            "/api/v1/projects",
            params={"skip": 0, "limit": 2},
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_projects_unauthorized(self, client: TestClient):
        response = client.get("/api/v1/projects")
        assert response.status_code == 403


class TestGetProject:
    def test_get_project_success(self, client: TestClient, auth_headers: dict, test_project: Project):
        response = client.get(f"/api/v1/projects/{test_project.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_project.id
        assert data["name"] == test_project.name

    def test_get_project_not_found(self, client: TestClient, admin_auth_headers: dict):
        response = client.get("/api/v1/projects/9999", headers=admin_auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_project_unauthorized(self, client: TestClient, test_project: Project):
        response = client.get(f"/api/v1/projects/{test_project.id}")
        assert response.status_code == 403

    def test_get_project_non_member_access_denied(self, client: TestClient, db: Session, test_project: Project):
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

        response = client.get(f"/api/v1/projects/{test_project.id}", headers=headers)
        assert response.status_code == 403


class TestCreateProject:
    def test_create_project_as_pm(self, client: TestClient, pm_auth_headers: dict):
        response = client.post(
            "/api/v1/projects",
            json={
                "name": "New Project",
                "description": "New project description",
                "status": "planning"
            },
            headers=pm_auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Project"
        assert data["description"] == "New project description"
        assert data["status"] == "planning"

    def test_create_project_as_admin(self, client: TestClient, admin_auth_headers: dict):
        response = client.post(
            "/api/v1/projects",
            json={
                "name": "Admin Project",
                "status": "active"
            },
            headers=admin_auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Admin Project"

    def test_create_project_with_members(self, client: TestClient, admin_auth_headers: dict, test_user: User):
        response = client.post(
            "/api/v1/projects",
            json={
                "name": "Project with Members",
                "status": "planning",
                "member_ids": [test_user.id]
            },
            headers=admin_auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["members"]) == 1
        assert data["members"][0]["id"] == test_user.id

    def test_create_project_unauthorized(self, client: TestClient):
        response = client.post(
            "/api/v1/projects",
            json={"name": "Unauthorized Project", "status": "planning"}
        )
        assert response.status_code == 403

    def test_create_project_empty_name(self, client: TestClient, admin_auth_headers: dict):
        response = client.post(
            "/api/v1/projects",
            json={"name": "", "status": "planning"},
            headers=admin_auth_headers
        )
        assert response.status_code == 422


class TestUpdateProject:
    def test_update_project_as_owner(self, client: TestClient, auth_headers: dict, test_project: Project):
        response = client.put(
            f"/api/v1/projects/{test_project.id}",
            json={"name": "Updated Project Name"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Project Name"

    def test_update_project_status(self, client: TestClient, auth_headers: dict, test_project: Project):
        response = client.put(
            f"/api/v1/projects/{test_project.id}",
            json={"status": "completed"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_update_project_not_found(self, client: TestClient, admin_auth_headers: dict):
        response = client.put(
            "/api/v1/projects/9999",
            json={"name": "Nonexistent"},
            headers=admin_auth_headers
        )
        assert response.status_code == 404

    def test_update_project_unauthorized(self, client: TestClient, test_project: Project):
        response = client.put(
            f"/api/v1/projects/{test_project.id}",
            json={"name": "Unauthorized Update"}
        )
        assert response.status_code == 403

    def test_update_project_non_owner_denied(self, client: TestClient, db: Session, test_project: Project):
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
            f"/api/v1/projects/{test_project.id}",
            json={"name": "Unauthorized Update"},
            headers=headers
        )
        assert response.status_code == 403


class TestDeleteProject:
    def test_delete_project_as_owner(self, client: TestClient, auth_headers: dict, test_project: Project):
        response = client.delete(f"/api/v1/projects/{test_project.id}", headers=auth_headers)
        assert response.status_code == 204

        response = client.get(f"/api/v1/projects/{test_project.id}", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_project_as_admin(self, client: TestClient, admin_auth_headers: dict, db: Session, test_user: User):
        project = Project(
            name="Project to Delete",
            status=ProjectStatus.ACTIVE,
            owner_id=test_user.id,
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        response = client.delete(f"/api/v1/projects/{project.id}", headers=admin_auth_headers)
        assert response.status_code == 204

    def test_delete_project_not_found(self, client: TestClient, admin_auth_headers: dict):
        response = client.delete("/api/v1/projects/9999", headers=admin_auth_headers)
        assert response.status_code == 404

    def test_delete_project_unauthorized(self, client: TestClient, test_project: Project):
        response = client.delete(f"/api/v1/projects/{test_project.id}")
        assert response.status_code == 403

    def test_delete_project_non_owner_denied(self, client: TestClient, db: Session, test_project: Project):
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

        response = client.delete(f"/api/v1/projects/{test_project.id}", headers=headers)
        assert response.status_code == 403


class TestProjectMembers:
    def test_add_member_success(self, client: TestClient, auth_headers: dict, test_project: Project, db: Session):
        new_member = User(
            email="member@example.com",
            username="newmember",
            hashed_password="hashed",
            first_name="New",
            last_name="Member",
            role=UserRole.MEMBER,
            is_active=True,
        )
        db.add(new_member)
        db.commit()
        db.refresh(new_member)

        response = client.post(
            f"/api/v1/projects/{test_project.id}/members/{new_member.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        member_ids = [m["id"] for m in data["members"]]
        assert new_member.id in member_ids

    def test_add_member_already_exists(self, client: TestClient, auth_headers: dict, test_project: Project, db: Session, test_user: User):
        test_project.members.append(test_user)
        db.commit()

        response = client.post(
            f"/api/v1/projects/{test_project.id}/members/{test_user.id}",
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "already a member" in response.json()["detail"].lower()

    def test_add_member_user_not_found(self, client: TestClient, auth_headers: dict, test_project: Project):
        response = client.post(
            f"/api/v1/projects/{test_project.id}/members/9999",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_remove_member_success(self, client: TestClient, auth_headers: dict, test_project: Project, db: Session):
        member = User(
            email="remove@example.com",
            username="removemember",
            hashed_password="hashed",
            first_name="Remove",
            last_name="Member",
            role=UserRole.MEMBER,
            is_active=True,
        )
        db.add(member)
        db.commit()
        db.refresh(member)

        test_project.members.append(member)
        db.commit()

        response = client.delete(
            f"/api/v1/projects/{test_project.id}/members/{member.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        member_ids = [m["id"] for m in data["members"]]
        assert member.id not in member_ids

    def test_remove_member_not_in_project(self, client: TestClient, auth_headers: dict, test_project: Project, db: Session):
        non_member = User(
            email="nonmember@example.com",
            username="nonmember",
            hashed_password="hashed",
            first_name="Non",
            last_name="Member",
            role=UserRole.MEMBER,
            is_active=True,
        )
        db.add(non_member)
        db.commit()
        db.refresh(non_member)

        response = client.delete(
            f"/api/v1/projects/{test_project.id}/members/{non_member.id}",
            headers=auth_headers
        )
        assert response.status_code == 404
