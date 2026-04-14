import pytest
from httpx import AsyncClient
from app.models import User, UserRole


@pytest.mark.asyncio
class TestListUsers:
    async def test_list_users_as_admin(self, async_client: AsyncClient, async_admin_auth_headers: dict):
        response = await async_client.get("/api/v1/users", headers=async_admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_list_users_with_role_filter(self, async_client: AsyncClient, async_admin_auth_headers: dict):
        response = await async_client.get(
            "/api/v1/users",
            params={"role": "admin"},
            headers=async_admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for user in data:
            assert user["role"] == "admin"

    async def test_list_users_with_search(self, async_client: AsyncClient, async_admin_auth_headers: dict):
        response = await async_client.get(
            "/api/v1/users",
            params={"search": "admin"},
            headers=async_admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for user in data:
            assert "admin" in user["username"].lower() or "admin" in user["email"].lower()

    async def test_list_users_pagination(self, async_client: AsyncClient, async_admin_auth_headers: dict):
        response = await async_client.get(
            "/api/v1/users",
            params={"skip": 0, "limit": 2},
            headers=async_admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    async def test_list_users_unauthorized(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/users")
        assert response.status_code == 403


@pytest.mark.asyncio
class TestGetUser:
    async def test_get_user_self(self, async_client: AsyncClient, async_auth_headers: dict, async_test_user: User):
        response = await async_client.get(f"/api/v1/users/{async_test_user.id}", headers=async_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == async_test_user.id
        assert data["username"] == async_test_user.username

    async def test_get_user_as_admin(self, async_client: AsyncClient, async_admin_auth_headers: dict, async_test_user: User):
        response = await async_client.get(f"/api/v1/users/{async_test_user.id}", headers=async_admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == async_test_user.id

    async def test_get_user_as_pm(self, async_client: AsyncClient, async_pm_auth_headers: dict, async_test_user: User):
        response = await async_client.get(f"/api/v1/users/{async_test_user.id}", headers=async_pm_auth_headers)
        assert response.status_code == 200

    async def test_get_user_other_denied(self, async_client: AsyncClient, async_test_user: User, async_admin_user: User):
        from app.auth import create_access_token
        token = create_access_token(subject=async_test_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.get(f"/api/v1/users/{async_admin_user.id}", headers=headers)
        assert response.status_code == 403

    async def test_get_user_not_found(self, async_client: AsyncClient, async_admin_auth_headers: dict):
        response = await async_client.get("/api/v1/users/9999", headers=async_admin_auth_headers)
        assert response.status_code == 404


@pytest.mark.asyncio
class TestCreateUser:
    async def test_create_user_as_admin(self, async_client: AsyncClient, async_admin_auth_headers: dict):
        response = await async_client.post(
            "/api/v1/users",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "password123",
                "first_name": "New",
                "last_name": "User",
                "role": "member"
            },
            headers=async_admin_auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"

    async def test_create_user_duplicate_email(self, async_client: AsyncClient, async_admin_auth_headers: dict, async_test_user: User):
        response = await async_client.post(
            "/api/v1/users",
            json={
                "email": async_test_user.email,
                "username": "different",
                "password": "password123",
                "first_name": "Test",
                "last_name": "User",
                "role": "member"
            },
            headers=async_admin_auth_headers
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_create_user_duplicate_username(self, async_client: AsyncClient, async_admin_auth_headers: dict, async_test_user: User):
        response = await async_client.post(
            "/api/v1/users",
            json={
                "email": "different@example.com",
                "username": async_test_user.username,
                "password": "password123",
                "first_name": "Test",
                "last_name": "User",
                "role": "member"
            },
            headers=async_admin_auth_headers
        )
        assert response.status_code == 400

    async def test_create_user_short_password(self, async_client: AsyncClient, async_admin_auth_headers: dict):
        response = await async_client.post(
            "/api/v1/users",
            json={
                "email": "short@example.com",
                "username": "shortpass",
                "password": "short",
                "first_name": "Short",
                "last_name": "Password",
                "role": "member"
            },
            headers=async_admin_auth_headers
        )
        assert response.status_code == 422

    async def test_create_user_non_admin_denied(self, async_client: AsyncClient, async_auth_headers: dict):
        response = await async_client.post(
            "/api/v1/users",
            json={
                "email": "unauthorized@example.com",
                "username": "unauthorized",
                "password": "password123",
                "first_name": "Test",
                "last_name": "User",
                "role": "member"
            },
            headers=async_auth_headers
        )
        assert response.status_code == 403


@pytest.mark.asyncio
class TestUpdateUser:
    async def test_update_user_self(self, async_client: AsyncClient, async_auth_headers: dict, async_test_user: User):
        response = await async_client.put(
            f"/api/v1/users/{async_test_user.id}",
            json={"first_name": "Updated"},
            headers=async_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"

    async def test_update_user_email(self, async_client: AsyncClient, async_auth_headers: dict, async_test_user: User):
        response = await async_client.put(
            f"/api/v1/users/{async_test_user.id}",
            json={"email": "updated@example.com"},
            headers=async_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@example.com"

    async def test_update_user_role_as_admin(self, async_client: AsyncClient, async_admin_auth_headers: dict, async_test_user: User):
        response = await async_client.put(
            f"/api/v1/users/{async_test_user.id}",
            json={"role": "project_manager"},
            headers=async_admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "project_manager"

    async def test_update_user_role_non_admin_denied(self, async_client: AsyncClient, async_auth_headers: dict, async_test_user: User):
        response = await async_client.put(
            f"/api/v1/users/{async_test_user.id}",
            json={"role": "admin"},
            headers=async_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "member"

    async def test_update_user_not_found(self, async_client: AsyncClient, async_admin_auth_headers: dict):
        response = await async_client.put(
            "/api/v1/users/9999",
            json={"first_name": "Nonexistent"},
            headers=async_admin_auth_headers
        )
        assert response.status_code == 404

    async def test_update_other_user_denied(self, async_client: AsyncClient, async_test_user: User, async_admin_user: User):
        from app.auth import create_access_token
        token = create_access_token(subject=async_test_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.put(
            f"/api/v1/users/{async_admin_user.id}",
            json={"first_name": "Hacked"},
            headers=headers
        )
        assert response.status_code == 403


@pytest.mark.asyncio
class TestDeleteUser:
    async def test_delete_user_as_admin(self, async_client: AsyncClient, async_admin_auth_headers: dict, async_admin_user: User):
        response = await async_client.post(
            "/api/v1/users",
            json={
                "email": "delete@example.com",
                "username": "deleteuser",
                "password": "password123",
                "first_name": "Delete",
                "last_name": "User",
                "role": "member"
            },
            headers=async_admin_auth_headers
        )
        assert response.status_code == 201
        user_id = response.json()["id"]

        response = await async_client.delete(f"/api/v1/users/{user_id}", headers=async_admin_auth_headers)
        assert response.status_code == 204

    async def test_delete_self_denied(self, async_client: AsyncClient, async_admin_auth_headers: dict, async_admin_user: User):
        response = await async_client.delete(f"/api/v1/users/{async_admin_user.id}", headers=async_admin_auth_headers)
        assert response.status_code == 400
        assert "cannot delete your own" in response.json()["detail"].lower()

    async def test_delete_user_not_found(self, async_client: AsyncClient, async_admin_auth_headers: dict):
        response = await async_client.delete("/api/v1/users/9999", headers=async_admin_auth_headers)
        assert response.status_code == 404

    async def test_delete_user_non_admin_denied(self, async_client: AsyncClient, async_auth_headers: dict, async_test_user: User):
        response = await async_client.delete(f"/api/v1/users/{async_test_user.id}", headers=async_auth_headers)
        assert response.status_code == 403
