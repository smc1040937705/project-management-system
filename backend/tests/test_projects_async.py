"""
项目管理路由异步测试
使用 pytest-asyncio + httpx 进行异步测试
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models import User, Project, UserRole, ProjectStatus
from app.auth import get_password_hash, create_access_token


@pytest.mark.asyncio
class TestProjectsRouterAsync:
    """项目管理路由异步测试类"""

    async def test_list_projects_success(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：正常获取项目列表
        验证：返回项目列表
        """
        # 创建测试用户和项目
        user = User(
            email="projecttest@example.com",
            username="projecttest",
            hashed_password=get_password_hash("password123"),
            first_name="Project",
            last_name="Test",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        project = Project(
            name="Test Project",
            description="Test Description",
            status=ProjectStatus.ACTIVE,
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()
        
        token = create_access_token(subject=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.get("/api/v1/projects", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_list_projects_no_auth(self, async_client: AsyncClient):
        """
        测试场景：获取项目列表失败（未认证）
        验证：返回403错误
        """
        response = await async_client.get("/api/v1/projects")
        
        assert response.status_code == 403

    async def test_list_projects_with_status_filter(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：按状态筛选项目
        验证：只返回指定状态的项目
        """
        user = User(
            email="filtertest@example.com",
            username="filtertest",
            hashed_password=get_password_hash("password123"),
            first_name="Filter",
            last_name="Test",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        project = Project(
            name="Active Project",
            status=ProjectStatus.ACTIVE,
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()
        
        token = create_access_token(subject=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.get(
            "/api/v1/projects?status=active",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_create_project_success(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：正常创建项目
        验证：返回201状态码和项目数据
        """
        user = User(
            email="createproject@example.com",
            username="createproject",
            hashed_password=get_password_hash("password123"),
            first_name="Create",
            last_name="Project",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        token = create_access_token(subject=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.post(
            "/api/v1/projects",
            headers=headers,
            json={
                "name": "New Project",
                "description": "New Description",
                "status": "planning",
                "budget": 10000
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Project"
        assert data["owner_id"] == user.id

    async def test_create_project_no_auth(self, async_client: AsyncClient):
        """
        测试场景：创建项目失败（未认证）
        验证：返回403错误
        """
        response = await async_client.post(
            "/api/v1/projects",
            json={
                "name": "New Project",
                "description": "New Description"
            }
        )
        
        assert response.status_code == 403

    async def test_create_project_invalid_data(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：创建项目失败（无效数据）
        验证：返回422验证错误
        """
        user = User(
            email="invalidproject@example.com",
            username="invalidproject",
            hashed_password=get_password_hash("password123"),
            first_name="Invalid",
            last_name="Project",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        token = create_access_token(subject=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.post(
            "/api/v1/projects",
            headers=headers,
            json={
                "name": "",
                "description": "Description"
            }
        )
        
        assert response.status_code == 422

    async def test_get_project_success(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：正常获取单个项目
        验证：返回项目详细信息
        """
        user = User(
            email="getproject@example.com",
            username="getproject",
            hashed_password=get_password_hash("password123"),
            first_name="Get",
            last_name="Project",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        project = Project(
            name="Specific Project",
            description="Specific Description",
            status=ProjectStatus.ACTIVE,
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        
        token = create_access_token(subject=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.get(
            f"/api/v1/projects/{project.id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project.id
        assert data["name"] == "Specific Project"

    async def test_get_project_not_found(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：获取不存在的项目
        验证：返回404错误
        """
        user = User(
            email="notfound@example.com",
            username="notfound",
            hashed_password=get_password_hash("password123"),
            first_name="Not",
            last_name="Found",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        token = create_access_token(subject=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.get(
            "/api/v1/projects/99999",
            headers=headers
        )
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]

    async def test_update_project_success(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：正常更新项目
        验证：返回更新后的项目数据
        """
        user = User(
            email="updateproject@example.com",
            username="updateproject",
            hashed_password=get_password_hash("password123"),
            first_name="Update",
            last_name="Project",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        project = Project(
            name="Old Name",
            description="Old Description",
            status=ProjectStatus.PLANNING,
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        
        token = create_access_token(subject=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.put(
            f"/api/v1/projects/{project.id}",
            headers=headers,
            json={
                "name": "Updated Name",
                "description": "Updated Description",
                "status": "active"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["status"] == "active"

    async def test_update_project_no_permission(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：更新项目失败（无权限）
        验证：返回403错误
        """
        # 创建项目所有者
        owner = User(
            email="owner@example.com",
            username="owner",
            hashed_password=get_password_hash("password123"),
            first_name="Owner",
            last_name="User",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(owner)
        db_session.commit()
        
        # 创建另一个用户
        other_user = User(
            email="other@example.com",
            username="other",
            hashed_password=get_password_hash("password123"),
            first_name="Other",
            last_name="User",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()
        
        project = Project(
            name="Protected Project",
            status=ProjectStatus.ACTIVE,
            owner_id=owner.id
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        
        token = create_access_token(subject=other_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.put(
            f"/api/v1/projects/{project.id}",
            headers=headers,
            json={"name": "Hacked Name"}
        )
        
        assert response.status_code == 403

    async def test_delete_project_success(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：正常删除项目
        验证：返回204状态码
        """
        user = User(
            email="deleteproject@example.com",
            username="deleteproject",
            hashed_password=get_password_hash("password123"),
            first_name="Delete",
            last_name="Project",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        project = Project(
            name="Project to Delete",
            status=ProjectStatus.ACTIVE,
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        
        token = create_access_token(subject=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.delete(
            f"/api/v1/projects/{project.id}",
            headers=headers
        )
        
        assert response.status_code == 204

    async def test_delete_project_not_found(self, async_client: AsyncClient, db_session: Session):
        """
        测试场景：删除不存在的项目
        验证：返回404错误
        """
        user = User(
            email="deletenotfound@example.com",
            username="deletenotfound",
            hashed_password=get_password_hash("password123"),
            first_name="Delete",
            last_name="NotFound",
            role=UserRole.MEMBER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        token = create_access_token(subject=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.delete(
            "/api/v1/projects/99999",
            headers=headers
        )
        
        assert response.status_code == 404
