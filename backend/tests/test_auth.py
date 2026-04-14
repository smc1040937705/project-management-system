import pytest
from httpx import AsyncClient
from jose import jwt
from app.config import settings


class TestAuth:
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user):
        """测试登录成功 - 返回正确的 token 结构"""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "password123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
        payload = jwt.decode(data["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == str(test_user.id)

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """测试登录失败 - 密码错误"""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "wrongpassword"}
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"

    @pytest.mark.asyncio
    async def test_login_wrong_username(self, client: AsyncClient, test_user):
        """测试登录失败 - 用户名不存在"""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "password123"}
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"

    @pytest.mark.asyncio
    async def test_login_deactivated_user(self, client: AsyncClient, db_session, test_user):
        """测试登录失败 - 用户已被禁用"""
        test_user.is_active = False
        db_session.commit()
        
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "password123"}
        )
        
        assert response.status_code == 403
        assert response.json()["detail"] == "User account is deactivated"

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient, db_session):
        """测试注册成功"""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123",
            "first_name": "New",
            "last_name": "User",
            "role": "member"
        }
        
        response = await client.post(
            "/api/v1/auth/register",
            json=user_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """测试注册失败 - 邮箱已存在"""
        user_data = {
            "email": "test@example.com",
            "username": "differentuser",
            "password": "password123",
            "first_name": "New",
            "last_name": "User",
            "role": "member"
        }
        
        response = await client.post(
            "/api/v1/auth/register",
            json=user_data
        )
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Email or username already registered"

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient, test_user):
        """测试注册失败 - 用户名已存在"""
        user_data = {
            "email": "different@example.com",
            "username": "testuser",
            "password": "password123",
            "first_name": "New",
            "last_name": "User",
            "role": "member"
        }
        
        response = await client.post(
            "/api/v1/auth/register",
            json=user_data
        )
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Email or username already registered"

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """测试注册失败 - 无效的邮箱格式"""
        user_data = {
            "email": "invalid-email",
            "username": "newuser",
            "password": "password123",
            "first_name": "New",
            "last_name": "User",
            "role": "member"
        }
        
        response = await client.post(
            "/api/v1/auth/register",
            json=user_data
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_me_success(self, authenticated_client: AsyncClient, test_user):
        """测试获取当前用户信息成功"""
        response = await authenticated_client.get("/api/v1/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_get_me_no_token(self, client: AsyncClient):
        """测试获取当前用户失败 - 未提供 token"""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, client: AsyncClient):
        """测试获取当前用户失败 - token 无效"""
        client.headers["Authorization"] = "Bearer invalid-token"
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, test_user):
        """测试刷新 token 成功"""
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "password123"}
        )
        refresh_token = login_response.json()["refresh_token"]
        
        response = await client.post(
            f"/api/v1/auth/refresh?refresh_token={refresh_token}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """测试刷新 token 失败 - token 无效"""
        response = await client.post(
            "/api/v1/auth/refresh?refresh_token=invalid-token"
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid refresh token"

    @pytest.mark.asyncio
    async def test_refresh_token_deactivated_user(self, client: AsyncClient, db_session, test_user):
        """测试刷新 token 失败 - 用户已被禁用"""
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "password123"}
        )
        refresh_token = login_response.json()["refresh_token"]
        
        test_user.is_active = False
        db_session.commit()
        
        response = await client.post(
            f"/api/v1/auth/refresh?refresh_token={refresh_token}"
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid refresh token"

    @pytest.mark.asyncio
    async def test_register_role_admin(self, client: AsyncClient):
        """测试注册管理员用户"""
        user_data = {
            "email": "admin2@example.com",
            "username": "admin2",
            "password": "password123",
            "first_name": "Admin",
            "last_name": "Two",
            "role": "admin"
        }
        
        response = await client.post(
            "/api/v1/auth/register",
            json=user_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "admin"

    @pytest.mark.asyncio
    async def test_register_invalid_role(self, client: AsyncClient):
        """测试注册失败 - 无效的角色"""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123",
            "first_name": "New",
            "last_name": "User",
            "role": "invalid_role"
        }
        
        response = await client.post(
            "/api/v1/auth/register",
            json=user_data
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_last_login_updated(self, client: AsyncClient, test_user, db_session):
        """测试登录成功后更新 last_login 时间"""
        old_last_login = test_user.last_login
        
        await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "password123"}
        )
        
        db_session.refresh(test_user)
        assert test_user.last_login is not None
        assert test_user.last_login != old_last_login

    @pytest.mark.asyncio
    async def test_access_token_expiry(self, client: AsyncClient, test_user):
        """测试 access token 包含正确的过期时间"""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "password123"}
        )
        access_token = response.json()["access_token"]
        
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in payload
        assert payload["type"] == "access"

    @pytest.mark.asyncio
    async def test_refresh_token_type(self, client: AsyncClient, test_user):
        """测试 refresh token 包含正确的类型"""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "password123"}
        )
        refresh_token = response.json()["refresh_token"]
        
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["type"] == "refresh"
