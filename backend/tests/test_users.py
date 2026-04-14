import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models import User, UserRole


class TestUsers:
    """用户管理接口测试"""

    async def test_list_users_success(
        self,
        client: AsyncClient,
        test_user: User,
        user_auth_headers: dict
    ):
        """测试获取用户列表成功"""
        response = await client.get("/api/v1/users", headers=user_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    async def test_list_users_with_filters(
        self,
        client: AsyncClient,
        test_user: User,
        user_auth_headers: dict
    ):
        """测试带过滤参数获取用户列表"""
        params = {
            "role": "member",
            "is_active": "true",
            "search": "test",
            "skip": 0,
            "limit": 10
        }
        response = await client.get("/api/v1/users", headers=user_auth_headers, params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_users_invalid_limit(
        self,
        client: AsyncClient,
        user_auth_headers: dict
    ):
        """测试参数校验失败 - limit 超出范围"""
        response = await client.get("/api/v1/users", headers=user_auth_headers, params={"limit": 999})
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    async def test_list_users_no_auth(self, client: AsyncClient):
        """测试未认证获取用户列表"""
        response = await client.get("/api/v1/users")
        
        assert response.status_code in [401, 403]
        data = response.json()
        assert "detail" in data

    async def test_get_user_own_profile_success(
        self,
        client: AsyncClient,
        test_user: User,
        user_auth_headers: dict
    ):
        """测试获取当前用户信息成功"""
        response = await client.get(f"/api/v1/users/{test_user.id}", headers=user_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username

    async def test_get_user_other_user_as_member_forbidden(
        self,
        client: AsyncClient,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试普通成员获取其他用户信息被拒绝"""
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed",
            first_name="Other",
            last_name="User",
            role=UserRole.MEMBER
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        response = await client.get(f"/api/v1/users/{other_user.id}", headers=user_auth_headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Not enough permissions"

    async def test_get_user_as_admin_success(
        self,
        client: AsyncClient,
        db_session: Session,
        admin_auth_headers: dict
    ):
        """测试管理员获取其他用户信息成功"""
        other_user = User(
            email="other2@example.com",
            username="otheruser2",
            hashed_password="hashed",
            first_name="Other",
            last_name="User",
            role=UserRole.MEMBER
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        response = await client.get(f"/api/v1/users/{other_user.id}", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == other_user.id

    async def test_get_user_not_found(
        self,
        client: AsyncClient,
        admin_auth_headers: dict
    ):
        """测试获取不存在的用户"""
        response = await client.get("/api/v1/users/9999", headers=admin_auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "User not found"

    async def test_create_user_as_admin_success(
        self,
        client: AsyncClient,
        admin_auth_headers: dict
    ):
        """测试管理员创建用户成功"""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123",
            "first_name": "New",
            "last_name": "User",
            "role": "member"
        }
        response = await client.post("/api/v1/users", json=user_data, headers=admin_auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert "password" not in data

    async def test_create_user_duplicate_email(
        self,
        client: AsyncClient,
        db_session: Session,
        admin_auth_headers: dict
    ):
        """测试创建用户邮箱已存在"""
        existing_user = User(
            email="duplicate@example.com",
            username="existing",
            hashed_password="hashed",
            first_name="Existing",
            last_name="User",
            role=UserRole.MEMBER
        )
        db_session.add(existing_user)
        db_session.commit()

        user_data = {
            "email": "duplicate@example.com",
            "username": "newuser",
            "password": "password123",
            "first_name": "New",
            "last_name": "User",
            "role": "member"
        }
        response = await client.post("/api/v1/users", json=user_data, headers=admin_auth_headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Email or username already registered"

    async def test_create_user_as_member_forbidden(
        self,
        client: AsyncClient,
        user_auth_headers: dict
    ):
        """测试普通成员创建用户被拒绝"""
        user_data = {
            "email": "hacker@example.com",
            "username": "hacker",
            "password": "password123",
            "first_name": "Hacker",
            "last_name": "User",
            "role": "admin"
        }
        response = await client.post("/api/v1/users", json=user_data, headers=user_auth_headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Not enough permissions"

    async def test_update_own_profile_success(
        self,
        client: AsyncClient,
        test_user: User,
        user_auth_headers: dict
    ):
        """测试更新当前用户信息成功"""
        update_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        response = await client.put(f"/api/v1/users/{test_user.id}", json=update_data, headers=user_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"

    async def test_update_other_user_as_member_forbidden(
        self,
        client: AsyncClient,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试普通成员更新其他用户被拒绝"""
        other_user = User(
            email="target@example.com",
            username="targetuser",
            hashed_password="hashed",
            first_name="Target",
            last_name="User",
            role=UserRole.MEMBER
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        update_data = {"first_name": "Hacked"}
        response = await client.put(f"/api/v1/users/{other_user.id}", json=update_data, headers=user_auth_headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Not enough permissions"

    async def test_update_user_as_admin_success(
        self,
        client: AsyncClient,
        db_session: Session,
        admin_auth_headers: dict
    ):
        """测试管理员更新其他用户信息成功"""
        other_user = User(
            email="update@example.com",
            username="updateuser",
            hashed_password="hashed",
            first_name="Update",
            last_name="User",
            role=UserRole.MEMBER
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        update_data = {
            "role": "project_manager",
            "is_active": True
        }
        response = await client.put(f"/api/v1/users/{other_user.id}", json=update_data, headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "project_manager"

    async def test_update_user_not_found(
        self,
        client: AsyncClient,
        admin_auth_headers: dict
    ):
        """测试更新不存在的用户"""
        update_data = {"first_name": "Test"}
        response = await client.put("/api/v1/users/9999", json=update_data, headers=admin_auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "User not found"

    async def test_delete_user_as_admin_success(
        self,
        client: AsyncClient,
        db_session: Session,
        admin_user: User,
        admin_auth_headers: dict
    ):
        """测试管理员删除用户成功"""
        target_user = User(
            email="delete@example.com",
            username="deleteuser",
            hashed_password="hashed",
            first_name="Delete",
            last_name="User",
            role=UserRole.MEMBER
        )
        db_session.add(target_user)
        db_session.commit()
        db_session.refresh(target_user)

        response = await client.delete(f"/api/v1/users/{target_user.id}", headers=admin_auth_headers)
        
        assert response.status_code == 204
        
        db_session.refresh(target_user)
        assert target_user.is_active == False

    async def test_delete_user_self_forbidden(
        self,
        client: AsyncClient,
        admin_user: User,
        admin_auth_headers: dict
    ):
        """测试删除自己被拒绝"""
        response = await client.delete(f"/api/v1/users/{admin_user.id}", headers=admin_auth_headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Cannot delete your own account"

    async def test_delete_user_as_member_forbidden(
        self,
        client: AsyncClient,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试普通成员删除用户被拒绝"""
        target_user = User(
            email="victim@example.com",
            username="victim",
            hashed_password="hashed",
            first_name="Victim",
            last_name="User",
            role=UserRole.MEMBER
        )
        db_session.add(target_user)
        db_session.commit()
        db_session.refresh(target_user)

        response = await client.delete(f"/api/v1/users/{target_user.id}", headers=user_auth_headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Not enough permissions"

    async def test_delete_user_not_found(
        self,
        client: AsyncClient,
        admin_auth_headers: dict
    ):
        """测试删除不存在的用户"""
        response = await client.delete("/api/v1/users/9999", headers=admin_auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "User not found"
