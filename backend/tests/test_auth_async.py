"""
认证路由异步测试
使用 pytest-asyncio + httpx 进行异步测试
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models import User, UserRole
from app.auth import get_password_hash, create_access_token, verify_password


@pytest.mark.asyncio
class TestAuthRouterAsync:
    """认证路由异步测试类"""

    async def test_register_success(self, async_client: AsyncClient):
        """
        测试场景：正常注册新用户
        验证：返回201状态码和用户数据
        """
        response = await async_client.post(
            "/api/v1/auth/register",
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
        assert "id" in data

    async def test_register_duplicate_email(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：注册失败（邮箱已存在）
        验证：返回400错误
        """
        # 先创建一个用户
        user = User(
            email="existing@example.com",
            username="existinguser",
            hashed_password=get_password_hash("password123"),
            first_name="Existing",
            last_name="User",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "existing@example.com",
                "username": "newuser",
                "password": "password123",
                "first_name": "New",
                "last_name": "User",
                "role": "member"
            }
        )
        
        assert response.status_code == 400
        assert "Email or username already registered" in response.json()["detail"]

    async def test_register_duplicate_username(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：注册失败（用户名已存在）
        验证：返回400错误
        """
        # 先创建一个用户
        user = User(
            email="existing2@example.com",
            username="existinguser2",
            hashed_password=get_password_hash("password123"),
            first_name="Existing",
            last_name="User",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "newemail@example.com",
                "username": "existinguser2",
                "password": "password123",
                "first_name": "New",
                "last_name": "User",
                "role": "member"
            }
        )
        
        assert response.status_code == 400
        assert "Email or username already registered" in response.json()["detail"]

    async def test_register_invalid_password(self, async_client: AsyncClient):
        """
        测试场景：注册失败（密码太短）
        验证：返回422验证错误
        """
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "short",
                "first_name": "New",
                "last_name": "User",
                "role": "member"
            }
        )
        
        assert response.status_code == 422

    async def test_login_success(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：正常登录
        验证：返回access_token和refresh_token
        """
        # 创建测试用户
        user = User(
            email="logintest@example.com",
            username="logintest",
            hashed_password=get_password_hash("password123"),
            first_name="Login",
            last_name="Test",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "logintest",
                "password": "password123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：登录失败（无效凭据）
        验证：返回401错误
        """
        # 创建测试用户
        user = User(
            email="logintest2@example.com",
            username="logintest2",
            hashed_password=get_password_hash("password123"),
            first_name="Login",
            last_name="Test",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "logintest2",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        """
        测试场景：登录失败（用户不存在）
        验证：返回401错误
        """
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    async def test_get_me_success(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：正常获取当前用户信息
        验证：返回当前用户数据
        """
        # 创建测试用户
        user = User(
            email="metest@example.com",
            username="metest",
            hashed_password=get_password_hash("password123"),
            first_name="Me",
            last_name="Test",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        token = create_access_token(subject=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user.id
        assert data["email"] == user.email
        assert data["username"] == user.username

    async def test_get_me_no_auth(self, async_client: AsyncClient):
        """
        测试场景：获取当前用户信息失败（未认证）
        验证：返回403错误
        """
        response = await async_client.get("/api/v1/auth/me")
        
        assert response.status_code == 403

    async def test_get_me_invalid_token(self, async_client: AsyncClient):
        """
        测试场景：获取当前用户信息失败（无效token）
        验证：返回401或403错误
        """
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code in [401, 403]

    async def test_refresh_token_success(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：正常刷新token
        验证：返回新的access_token和refresh_token
        """
        from app.auth import create_refresh_token
        
        # 创建测试用户
        user = User(
            email="refreshtest@example.com",
            username="refreshtest",
            hashed_password=get_password_hash("password123"),
            first_name="Refresh",
            last_name="Test",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        refresh_token = create_refresh_token(subject=user.id)

        response = await async_client.post(
            "/api/v1/auth/refresh",
            params={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_token_invalid(self, async_client: AsyncClient):
        """
        测试场景：刷新token失败（无效token）
        验证：返回401错误
        """
        response = await async_client.post(
            "/api/v1/auth/refresh",
            params={"refresh_token": "invalid_token"}
        )
        
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]


@pytest.mark.asyncio
class TestAuthUtilsAsync:
    """认证工具函数异步测试类"""

    async def test_password_hashing(self):
        """
        测试场景：密码哈希和验证
        验证：哈希后的密码可以正确验证
        """
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    async def test_password_hash_different_each_time(self):
        """
        测试场景：相同密码每次哈希结果不同
        验证：两次哈希结果不同但都可用
        """
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
