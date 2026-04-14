import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, UserRole
from app.auth import get_password_hash


class TestUsersRouter:
    """用户管理路由测试类"""

    def test_list_users_success(self, client: TestClient, test_user: User, auth_headers: dict):
        """
        测试场景：正常获取用户列表
        验证：返回用户列表
        """
        response = client.get("/api/v1/users", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_users_no_auth(self, client: TestClient):
        """
        测试场景：获取用户列表失败（未认证）
        验证：返回403错误
        """
        response = client.get("/api/v1/users")
        
        assert response.status_code == 403

    def test_list_users_with_role_filter(self, client: TestClient, test_admin: User, auth_headers: dict):
        """
        测试场景：按角色筛选用户
        验证：只返回匹配角色的用户
        """
        response = client.get("/api/v1/users?role=admin", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for user in data:
            assert user["role"] == "admin"

    def test_list_users_with_is_active_filter(self, client: TestClient, test_user: User, auth_headers: dict):
        """
        测试场景：按激活状态筛选用户
        验证：只返回匹配状态的用户
        """
        response = client.get("/api/v1/users?is_active=true", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for user in data:
            assert user["is_active"] is True

    def test_list_users_with_search(self, client: TestClient, test_user: User, auth_headers: dict):
        """
        测试场景：搜索用户
        验证：返回匹配搜索词的用户
        """
        response = client.get("/api/v1/users?search=test", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_user_success(self, client: TestClient, test_user: User, auth_headers: dict):
        """
        测试场景：正常获取单个用户
        验证：返回用户详细信息
        """
        response = client.get(f"/api/v1/users/{test_user.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username

    def test_get_user_not_found(self, client: TestClient, admin_auth_headers: dict):
        """
        测试场景：获取不存在的用户
        验证：返回404错误
        """
        response = client.get("/api/v1/users/99999", headers=admin_auth_headers)
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_get_user_no_permission(self, client: TestClient, db_session: Session, auth_headers: dict):
        """
        测试场景：获取用户信息失败（无权限查看其他用户）
        验证：普通用户不能查看其他用户详情
        """
        # 创建另一个用户
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

        response = client.get(f"/api/v1/users/{other_user.id}", headers=auth_headers)
        
        assert response.status_code == 403

    def test_create_user_success(self, client: TestClient, admin_auth_headers: dict):
        """
        测试场景：管理员正常创建用户
        验证：返回201状态码和用户数据
        """
        response = client.post(
            "/api/v1/users",
            headers=admin_auth_headers,
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "password123",
                "first_name": "New",
                "last_name": "User",
                "role": "member"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert data["role"] == "member"
        assert "id" in data

    def test_create_user_no_permission(self, client: TestClient, auth_headers: dict):
        """
        测试场景：创建用户失败（非管理员）
        验证：返回403错误
        """
        response = client.post(
            "/api/v1/users",
            headers=auth_headers,
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "password123",
                "first_name": "New",
                "last_name": "User",
                "role": "member"
            }
        )
        
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    def test_create_user_duplicate_email(self, client: TestClient, test_user: User, admin_auth_headers: dict):
        """
        测试场景：创建用户失败（邮箱已存在）
        验证：返回400错误
        """
        response = client.post(
            "/api/v1/users",
            headers=admin_auth_headers,
            json={
                "email": "test@example.com",  # 已存在的邮箱
                "username": "newuser123",
                "password": "password123",
                "first_name": "New",
                "last_name": "User",
                "role": "member"
            }
        )
        
        assert response.status_code == 400
        assert "Email or username already registered" in response.json()["detail"]

    def test_update_user_success(self, client: TestClient, test_user: User, auth_headers: dict):
        """
        测试场景：正常更新自己的信息
        验证：返回更新后的用户数据
        """
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers,
            json={
                "first_name": "Updated",
                "last_name": "Name"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"

    def test_update_user_by_admin(self, client: TestClient, test_user: User, admin_auth_headers: dict):
        """
        测试场景：管理员更新其他用户信息
        验证：返回更新后的用户数据
        """
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            headers=admin_auth_headers,
            json={
                "role": "admin",
                "is_active": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"
        assert data["is_active"] is False

    def test_update_user_no_permission(self, client: TestClient, db_session: Session, auth_headers: dict):
        """
        测试场景：更新用户失败（无权限）
        验证：普通用户不能更新其他用户信息
        """
        # 创建另一个用户
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

        response = client.put(
            f"/api/v1/users/{other_user.id}",
            headers=auth_headers,
            json={"first_name": "Updated"}
        )
        
        assert response.status_code == 403

    def test_update_user_not_found(self, client: TestClient, admin_auth_headers: dict):
        """
        测试场景：更新不存在的用户
        验证：返回404错误
        """
        response = client.put(
            "/api/v1/users/99999",
            headers=admin_auth_headers,
            json={"first_name": "Updated"}
        )
        
        assert response.status_code == 404

    def test_update_user_duplicate_email(self, client: TestClient, test_user: User, db_session: Session, auth_headers: dict):
        """
        测试场景：更新用户失败（邮箱已存在）
        验证：返回400错误
        """
        # 创建另一个用户
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

        response = client.put(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers,
            json={"email": "other@example.com"}  # 已存在的邮箱
        )
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_delete_user_success(self, client: TestClient, db_session: Session, admin_auth_headers: dict):
        """
        测试场景：管理员正常删除（禁用）用户
        验证：返回204状态码
        """
        # 创建一个用于删除测试的用户
        user_to_delete = User(
            email="delete@example.com",
            username="deleteuser",
            hashed_password=get_password_hash("password123"),
            first_name="Delete",
            last_name="User",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user_to_delete)
        db_session.commit()

        response = client.delete(
            f"/api/v1/users/{user_to_delete.id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 204

        # 验证用户被禁用
        db_session.refresh(user_to_delete)
        assert user_to_delete.is_active is False

    def test_delete_user_no_permission(self, client: TestClient, db_session: Session, auth_headers: dict):
        """
        测试场景：删除用户失败（非管理员）
        验证：返回403错误
        """
        # 创建另一个用户
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

        response = client.delete(
            f"/api/v1/users/{other_user.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 403

    def test_delete_user_not_found(self, client: TestClient, admin_auth_headers: dict):
        """
        测试场景：删除不存在的用户
        验证：返回404错误
        """
        response = client.delete("/api/v1/users/99999", headers=admin_auth_headers)
        
        assert response.status_code == 404

    def test_delete_self_fail(self, client: TestClient, test_admin: User, admin_auth_headers: dict):
        """
        测试场景：删除自己失败
        验证：返回400错误
        """
        response = client.delete(
            f"/api/v1/users/{test_admin.id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 400
        assert "Cannot delete your own account" in response.json()["detail"]

    def test_pm_can_view_all_users(self, client: TestClient, pm_auth_headers: dict):
        """
        测试场景：项目经理可以查看所有用户
        验证：项目经理能获取用户列表
        """
        response = client.get("/api/v1/users", headers=pm_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_pm_can_view_other_user(self, client: TestClient, test_user: User, pm_auth_headers: dict):
        """
        测试场景：项目经理可以查看其他用户详情
        验证：项目经理能获取其他用户信息
        """
        response = client.get(f"/api/v1/users/{test_user.id}", headers=pm_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
