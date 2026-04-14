import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import User, UserRole
from app.auth import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token


class TestLogin:
    def test_login_success(self, client: TestClient, test_user: User):
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
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "password123"}
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_inactive_user(self, client: TestClient, db: Session):
        inactive_user = User(
            email="inactive@example.com",
            username="inactiveuser",
            hashed_password=get_password_hash("password123"),
            first_name="Inactive",
            last_name="User",
            role=UserRole.MEMBER,
            is_active=False,
        )
        db.add(inactive_user)
        db.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={"username": "inactiveuser", "password": "password123"}
        )
        assert response.status_code == 403
        assert "deactivated" in response.json()["detail"].lower()


class TestRegister:
    def test_register_success(self, client: TestClient):
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
        assert data["first_name"] == "New"
        assert data["last_name"] == "User"
        assert "id" in data

    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "anotheruser",
                "password": "password123",
                "first_name": "Another",
                "last_name": "User",
                "role": "member"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_duplicate_username(self, client: TestClient, test_user: User):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "another@example.com",
                "username": "testuser",
                "password": "password123",
                "first_name": "Another",
                "last_name": "User",
                "role": "member"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_short_password(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "shortpw@example.com",
                "username": "shortpw",
                "password": "short",
                "first_name": "Short",
                "last_name": "Password",
                "role": "member"
            }
        )
        assert response.status_code == 422

    def test_register_invalid_email(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "username": "invalidemail",
                "password": "password123",
                "first_name": "Invalid",
                "last_name": "Email",
                "role": "member"
            }
        )
        assert response.status_code == 422


class TestGetMe:
    def test_get_me_success(self, client: TestClient, auth_headers: dict):
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_get_me_no_token(self, client: TestClient):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 403

    def test_get_me_invalid_token(self, client: TestClient):
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_get_me_expired_token(self, client: TestClient):
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"}
        )
        assert response.status_code == 401


class TestRefreshToken:
    def test_refresh_token_success(self, client: TestClient, test_user: User):
        refresh_token = create_refresh_token(test_user.id)
        response = client.post(
            "/api/v1/auth/refresh",
            params={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_invalid(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/refresh",
            params={"refresh_token": "invalid_token"}
        )
        assert response.status_code == 401

    def test_refresh_token_user_not_found(self, client: TestClient, db: Session):
        refresh_token = create_refresh_token(9999)
        response = client.post(
            "/api/v1/auth/refresh",
            params={"refresh_token": refresh_token}
        )
        assert response.status_code == 401


class TestAuthUtilities:
    def test_password_hashing(self):
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrongpassword", hashed)

    def test_create_access_token(self, test_user: User):
        token = create_access_token(subject=test_user.id)
        assert token is not None
        payload = decode_token(token)
        assert payload is not None
        assert payload.sub == test_user.id

    def test_create_refresh_token(self, test_user: User):
        token = create_refresh_token(subject=test_user.id)
        assert token is not None
        payload = decode_token(token)
        assert payload is not None
        assert payload.sub == test_user.id

    def test_decode_invalid_token(self):
        payload = decode_token("invalid_token")
        assert payload is None
