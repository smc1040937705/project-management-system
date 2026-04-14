import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, Project, UserRole, ProjectStatus


class TestProjectsRouter:
    """项目路由测试类"""

    def test_list_projects_success(self, client: TestClient, test_project: Project, auth_headers: dict):
        """
        测试场景：正常获取项目列表
        验证：返回项目列表
        """
        response = client.get("/api/v1/projects", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_projects_no_auth(self, client: TestClient):
        """
        测试场景：获取项目列表失败（未认证）
        验证：返回403错误
        """
        response = client.get("/api/v1/projects")
        
        assert response.status_code == 403

    def test_list_projects_with_pagination(self, client: TestClient, test_project: Project, auth_headers: dict):
        """
        测试场景：分页获取项目列表
        验证：正确应用skip和limit参数
        """
        response = client.get("/api/v1/projects?skip=0&limit=10", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_projects_with_status_filter(self, client: TestClient, test_project: Project, auth_headers: dict):
        """
        测试场景：按状态筛选项目
        验证：只返回匹配状态的项目
        """
        response = client.get("/api/v1/projects?status=active", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for project in data:
            assert project["status"] == "active"

    def test_list_projects_with_search(self, client: TestClient, test_project: Project, auth_headers: dict):
        """
        测试场景：搜索项目
        验证：返回匹配搜索词的项目
        """
        response = client.get("/api/v1/projects?search=Test", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_project_success(self, client: TestClient, test_project: Project, auth_headers: dict):
        """
        测试场景：正常获取单个项目
        验证：返回项目详细信息
        """
        response = client.get(f"/api/v1/projects/{test_project.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_project.id
        assert data["name"] == test_project.name
        assert "owner" in data
        assert "members" in data

    def test_get_project_not_found(self, client: TestClient, auth_headers: dict):
        """
        测试场景：获取不存在的项目
        验证：返回404错误
        """
        response = client.get("/api/v1/projects/99999", headers=auth_headers)
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]

    def test_get_project_no_permission(self, client: TestClient, db_session: Session, auth_headers: dict):
        """
        测试场景：获取项目失败（无权限）
        验证：返回403错误
        """
        # 创建另一个用户和项目
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
            description="Other Description",
            status=ProjectStatus.ACTIVE,
            owner_id=other_user.id
        )
        db_session.add(other_project)
        db_session.commit()

        response = client.get(f"/api/v1/projects/{other_project.id}", headers=auth_headers)
        
        assert response.status_code == 403

    def test_create_project_success(self, client: TestClient, auth_headers: dict):
        """
        测试场景：正常创建项目
        验证：返回201状态码和项目数据
        """
        response = client.post(
            "/api/v1/projects",
            headers=auth_headers,
            json={
                "name": "New Project",
                "description": "New Description",
                "status": "planning"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Project"
        assert data["status"] == "planning"
        assert "id" in data

    def test_create_project_validation_error(self, client: TestClient, auth_headers: dict):
        """
        测试场景：创建项目失败（验证错误）
        验证：返回422错误
        """
        response = client.post(
            "/api/v1/projects",
            headers=auth_headers,
            json={
                "name": "",  # 空名称
                "status": "planning"
            }
        )
        
        assert response.status_code == 422

    def test_create_project_no_auth(self, client: TestClient):
        """
        测试场景：创建项目失败（未认证）
        验证：返回403错误
        """
        response = client.post(
            "/api/v1/projects",
            json={
                "name": "New Project",
                "status": "planning"
            }
        )
        
        assert response.status_code == 403

    def test_update_project_success(self, client: TestClient, test_project: Project, auth_headers: dict):
        """
        测试场景：正常更新项目
        验证：返回更新后的项目数据
        """
        response = client.put(
            f"/api/v1/projects/{test_project.id}",
            headers=auth_headers,
            json={
                "name": "Updated Project Name",
                "status": "completed"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Project Name"
        assert data["status"] == "completed"

    def test_update_project_not_found(self, client: TestClient, auth_headers: dict):
        """
        测试场景：更新不存在的项目
        验证：返回404错误
        """
        response = client.put(
            "/api/v1/projects/99999",
            headers=auth_headers,
            json={"name": "Updated Name"}
        )
        
        assert response.status_code == 404

    def test_update_project_no_permission(self, client: TestClient, db_session: Session, auth_headers: dict):
        """
        测试场景：更新项目失败（无权限）
        验证：返回403错误
        """
        # 创建另一个用户和项目
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

        response = client.put(
            f"/api/v1/projects/{other_project.id}",
            headers=auth_headers,
            json={"name": "Updated Name"}
        )
        
        assert response.status_code == 403

    def test_delete_project_success(self, client: TestClient, db_session: Session, test_user: User, auth_headers: dict):
        """
        测试场景：正常删除项目
        验证：返回204状态码
        """
        # 创建一个专门用于删除测试的项目
        project_to_delete = Project(
            name="Project To Delete",
            status=ProjectStatus.ACTIVE,
            owner_id=test_user.id
        )
        db_session.add(project_to_delete)
        db_session.commit()

        response = client.delete(
            f"/api/v1/projects/{project_to_delete.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204

    def test_delete_project_not_found(self, client: TestClient, auth_headers: dict):
        """
        测试场景：删除不存在的项目
        验证：返回404错误
        """
        response = client.delete("/api/v1/projects/99999", headers=auth_headers)
        
        assert response.status_code == 404

    def test_delete_project_no_permission(self, client: TestClient, db_session: Session, auth_headers: dict):
        """
        测试场景：删除项目失败（无权限）
        验证：返回403错误
        """
        # 创建另一个用户和项目
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

        response = client.delete(f"/api/v1/projects/{other_project.id}", headers=auth_headers)
        
        assert response.status_code == 403

    def test_add_member_success(self, client: TestClient, test_project: Project, db_session: Session, auth_headers: dict):
        """
        测试场景：正常添加项目成员
        验证：返回更新后的项目数据
        """
        # 创建要添加的成员
        new_member = User(
            email="member@example.com",
            username="member",
            hashed_password="hashed",
            first_name="Member",
            last_name="User",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(new_member)
        db_session.commit()

        response = client.post(
            f"/api/v1/projects/{test_project.id}/members/{new_member.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert any(m["id"] == new_member.id for m in data["members"])

    def test_add_member_project_not_found(self, client: TestClient, auth_headers: dict):
        """
        测试场景：添加成员失败（项目不存在）
        验证：返回404错误
        """
        response = client.post(
            "/api/v1/projects/99999/members/1",
            headers=auth_headers
        )
        
        assert response.status_code == 404

    def test_add_member_user_not_found(self, client: TestClient, test_project: Project, auth_headers: dict):
        """
        测试场景：添加成员失败（用户不存在）
        验证：返回404错误
        """
        response = client.post(
            f"/api/v1/projects/{test_project.id}/members/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404

    def test_remove_member_success(self, client: TestClient, test_project: Project, db_session: Session, auth_headers: dict):
        """
        测试场景：正常移除项目成员
        验证：成员从项目中移除
        """
        # 创建并添加成员
        member = User(
            email="member2@example.com",
            username="member2",
            hashed_password="hashed",
            first_name="Member",
            last_name="User",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(member)
        db_session.commit()

        # 先添加成员
        client.post(
            f"/api/v1/projects/{test_project.id}/members/{member.id}",
            headers=auth_headers
        )

        # 再移除成员
        response = client.delete(
            f"/api/v1/projects/{test_project.id}/members/{member.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200

    def test_admin_can_access_all_projects(self, client: TestClient, db_session: Session, admin_auth_headers: dict):
        """
        测试场景：管理员可以访问所有项目
        验证：管理员能获取其他用户的项目
        """
        # 创建另一个用户的项目
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

        response = client.get(f"/api/v1/projects/{other_project.id}", headers=admin_auth_headers)
        
        assert response.status_code == 200
        assert response.json()["id"] == other_project.id
