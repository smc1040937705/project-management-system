import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, UserRole
from app.auth import verify_password, get_password_hash, create_access_token, decode_token


class TestAuthRouter:
    """认证路由测试类"""

    def test_login_success(self, client: TestClient, test_user: User):
        """
        测试场景：正常登录成功
        验证：返回access_token和refresh_token
        """
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "password123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """
        测试场景：登录失败（密码错误）
        验证：返回401未授权错误
        """
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "wrongpassword"}
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        """
        测试场景：登录失败（用户不存在）
        验证：返回401未授权错误
        """
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "password123"}
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_inactive_user(self, client: TestClient, db_session: Session):
        """
        测试场景：登录失败（用户被禁用）
        验证：返回403禁止访问错误
        """
        # 创建被禁用的用户
        inactive_user = User(
            email="inactive@example.com",
            username="inactive",
            hashed_password=get_password_hash("password123"),
            first_name="Inactive",
            last_name="User",
            role=UserRole.MEMBER,
            is_active=False
        )
        db_session.add(inactive_user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={"username": "inactive", "password": "password123"}
        )
        
        assert response.status_code == 403
        assert "User account is deactivated" in response.json()["detail"]

    def test_register_success(self, client: TestClient):
        """
        测试场景：正常注册成功
        验证：返回201状态码和用户数据
        """
        response = client.post(
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
        assert data["role"] == "member"
        assert "id" in data

    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """
        测试场景：注册失败（邮箱已存在）
        验证：返回400错误
        """
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",  # 已存在的邮箱
                "username": "newuser2",
                "password": "password123",
                "first_name": "New",
                "last_name": "User",
                "role": "member"
            }
        )
        
        assert response.status_code == 400
        assert "Email or username already registered" in response.json()["detail"]

    def test_register_duplicate_username(self, client: TestClient, test_user: User):
        """
        测试场景：注册失败（用户名已存在）
        验证：返回400错误
        """
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newemail@example.com",
                "username": "testuser",  # 已存在的用户名
                "password": "password123",
                "first_name": "New",
                "last_name": "User",
                "role": "member"
            }
        )
        
        assert response.status_code == 400
        assert "Email or username already registered" in response.json()["detail"]

    def test_register_invalid_password(self, client: TestClient):
        """
        测试场景：注册失败（密码太短）
        验证：返回422验证错误
        """
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "short",  # 密码太短
                "first_name": "New",
                "last_name": "User",
                "role": "member"
            }
        )
        
        assert response.status_code == 422

    def test_get_me_success(self, client: TestClient, test_user: User, auth_headers: dict):
        """
        测试场景：正常获取当前用户信息
        验证：返回当前用户数据
        """
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username

    def test_get_me_no_auth(self, client: TestClient):
        """
        测试场景：获取当前用户信息失败（未认证）
        验证：返回401错误
        """
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 403

    def test_get_me_invalid_token(self, client: TestClient):
        """
        测试场景：获取当前用户信息失败（无效token）
        验证：返回401或403错误
        """
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        # FastAPI的HTTPBearer在token无效时返回401或403
        assert response.status_code in [401, 403]

    def test_refresh_token_success(self, client: TestClient, test_user: User):
        """
        测试场景：正常刷新token
        验证：返回新的access_token和refresh_token
        """
        from app.auth import create_refresh_token
        
        refresh_token = create_refresh_token(subject=test_user.id)
        
        response = client.post(
            "/api/v1/auth/refresh",
            params={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_invalid(self, client: TestClient):
        """
        测试场景：刷新token失败（无效token）
        验证：返回401错误
        """
        response = client.post(
            "/api/v1/auth/refresh",
            params={"refresh_token": "invalid_token"}
        )
        
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]


class TestAuthUtils:
    """认证工具函数测试类"""

    def test_verify_password_correct(self):
        """
        测试场景：验证密码正确
        验证：返回True
        """
        hashed = get_password_hash("password123")
        assert verify_password("password123", hashed) is True

    def test_verify_password_incorrect(self):
        """
        测试场景：验证密码错误
        验证：返回False
        """
        hashed = get_password_hash("password123")
        assert verify_password("wrongpassword", hashed) is False

    def test_create_and_decode_access_token(self):
        """
        测试场景：创建和解析access token
        验证：token能被正确解析
        """
        token = create_access_token(subject=1)
        payload = decode_token(token)
        
        assert payload is not None
        assert payload.sub == 1

    def test_decode_invalid_token(self):
        """
        测试场景：解析无效token
        验证：返回None
        """
        payload = decode_token("invalid_token")
        assert payload is None

    def test_get_password_hash_different_each_time(self):
        """
        测试场景：相同密码生成不同hash
        验证：两次hash不同但都验证通过
        """
        password = "password123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
