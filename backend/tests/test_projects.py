import pytest
from httpx import AsyncClient
from app.models import ProjectStatus


class TestProjects:
    @pytest.mark.asyncio
    async def test_list_projects_success(self, authenticated_client: AsyncClient, test_project):
        """测试获取项目列表成功"""
        response = await authenticated_client.get("/api/v1/projects")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["id"] == test_project.id
        assert data[0]["name"] == test_project.name

    @pytest.mark.asyncio
    async def test_list_projects_pagination(self, authenticated_client: AsyncClient, db_session, test_user):
        """测试项目列表分页功能"""
        for i in range(5):
            from app.models import Project
            project = Project(
                name=f"Project {i}",
                description=f"Description {i}",
                status=ProjectStatus.ACTIVE,
                owner_id=test_user.id
            )
            db_session.add(project)
        db_session.commit()
        
        response = await authenticated_client.get("/api/v1/projects?skip=0&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_list_projects_filter_status(self, authenticated_client: AsyncClient, db_session, test_user):
        """测试按状态过滤项目"""
        from app.models import Project
        active_project = Project(
            name="Active Project",
            status=ProjectStatus.ACTIVE,
            owner_id=test_user.id
        )
        completed_project = Project(
            name="Completed Project",
            status=ProjectStatus.COMPLETED,
            owner_id=test_user.id
        )
        db_session.add_all([active_project, completed_project])
        db_session.commit()
        
        response = await authenticated_client.get("/api/v1/projects?status=completed")
        
        assert response.status_code == 200
        data = response.json()
        for project in data:
            assert project["status"] == "completed"

    @pytest.mark.asyncio
    async def test_list_projects_search(self, authenticated_client: AsyncClient, db_session, test_user):
        """测试搜索项目"""
        from app.models import Project
        project1 = Project(
            name="Unique Project Name",
            description="Test Description",
            status=ProjectStatus.ACTIVE,
            owner_id=test_user.id
        )
        project2 = Project(
            name="Another Project",
            description="Contains Unique Keyword",
            status=ProjectStatus.ACTIVE,
            owner_id=test_user.id
        )
        db_session.add_all([project1, project2])
        db_session.commit()
        
        response = await authenticated_client.get("/api/v1/projects?search=Unique")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    @pytest.mark.asyncio
    async def test_list_projects_no_token(self, client: AsyncClient):
        """测试获取项目列表失败 - 未认证"""
        response = await client.get("/api/v1/projects")
        
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_project_success(self, authenticated_client: AsyncClient, test_project):
        """测试获取单个项目成功"""
        response = await authenticated_client.get(f"/api/v1/projects/{test_project.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_project.id
        assert data["name"] == test_project.name
        assert "task_count" in data
        assert "completed_task_count" in data

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, authenticated_client: AsyncClient):
        """测试获取项目失败 - 项目不存在"""
        response = await authenticated_client.get("/api/v1/projects/99999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Project not found"

    @pytest.mark.asyncio
    async def test_get_project_no_permission(self, client: AsyncClient, db_session):
        """测试获取项目失败 - 无权限访问"""
        from app.models import User, Project
        from app.auth import get_password_hash
        user1 = User(
            email="user1@example.com",
            username="user1",
            hashed_password=get_password_hash("password123"),
            first_name="User",
            last_name="One",
            is_active=True
        )
        user2 = User(
            email="user2@example.com",
            username="user2",
            hashed_password=get_password_hash("password123"),
            first_name="User",
            last_name="Two",
            is_active=True
        )
        db_session.add_all([user1, user2])
        db_session.commit()
        
        project = Project(
            name="Private Project",
            status=ProjectStatus.ACTIVE,
            owner_id=user1.id
        )
        db_session.add(project)
        db_session.commit()
        
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "user2", "password": "password123"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
        
        response = await client.get(f"/api/v1/projects/{project.id}")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_project_success(self, authenticated_client: AsyncClient):
        """测试创建项目成功"""
        project_data = {
            "name": "New Project",
            "description": "New Project Description",
            "status": "active",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "budget": 50000.0,
            "member_ids": []
        }
        
        response = await authenticated_client.post(
            "/api/v1/projects",
            json=project_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == project_data["name"]
        assert data["description"] == project_data["description"]
        assert data["budget"] == project_data["budget"]

    @pytest.mark.asyncio
    async def test_create_project_with_members(self, authenticated_client: AsyncClient, db_session, test_user):
        """测试创建项目并添加成员"""
        from app.models import User
        from app.auth import get_password_hash
        member = User(
            email="member@example.com",
            username="member1",
            hashed_password=get_password_hash("password123"),
            first_name="Member",
            last_name="One",
            is_active=True
        )
        db_session.add(member)
        db_session.commit()
        
        project_data = {
            "name": "Project with Members",
            "description": "Test",
            "status": "active",
            "member_ids": [member.id]
        }
        
        response = await authenticated_client.post(
            "/api/v1/projects",
            json=project_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert len(data["members"]) == 1

    @pytest.mark.asyncio
    async def test_create_project_missing_name(self, authenticated_client: AsyncClient):
        """测试创建项目失败 - 缺少名称"""
        project_data = {
            "description": "Missing name",
            "status": "active"
        }
        
        response = await authenticated_client.post(
            "/api/v1/projects",
            json=project_data
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_project_success(self, authenticated_client: AsyncClient, test_project):
        """测试更新项目成功"""
        update_data = {
            "name": "Updated Project Name",
            "description": "Updated Description",
            "status": "on_hold",
            "budget": 20000.0
        }
        
        response = await authenticated_client.put(
            f"/api/v1/projects/{test_project.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["status"] == "on_hold"
        assert data["budget"] == 20000.0

    @pytest.mark.asyncio
    async def test_update_project_partial(self, authenticated_client: AsyncClient, test_project):
        """测试部分更新项目"""
        update_data = {
            "name": "Only Name Updated"
        }
        
        response = await authenticated_client.put(
            f"/api/v1/projects/{test_project.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Only Name Updated"
        assert data["description"] == test_project.description

    @pytest.mark.asyncio
    async def test_update_project_not_found(self, authenticated_client: AsyncClient):
        """测试更新项目失败 - 项目不存在"""
        update_data = {"name": "Not Found"}
        
        response = await authenticated_client.put(
            "/api/v1/projects/99999",
            json=update_data
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_project_no_permission(self, client: AsyncClient, db_session):
        """测试更新项目失败 - 无权限"""
        from app.models import User, Project
        from app.auth import get_password_hash
        owner = User(
            email="owner@example.com",
            username="owner",
            hashed_password=get_password_hash("password123"),
            first_name="Owner",
            last_name="User",
            is_active=True
        )
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password=get_password_hash("password123"),
            first_name="Other",
            last_name="User",
            is_active=True
        )
        db_session.add_all([owner, other_user])
        db_session.commit()
        
        project = Project(
            name="Owner's Project",
            status=ProjectStatus.ACTIVE,
            owner_id=owner.id
        )
        db_session.add(project)
        db_session.commit()
        
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "otheruser", "password": "password123"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
        
        response = await client.put(
            f"/api/v1/projects/{project.id}",
            json={"name": "Hacked Name"}
        )
        
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_project_success(self, authenticated_client: AsyncClient, test_project):
        """测试删除项目成功"""
        response = await authenticated_client.delete(
            f"/api/v1/projects/{test_project.id}"
        )
        
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, authenticated_client: AsyncClient):
        """测试删除项目失败 - 项目不存在"""
        response = await authenticated_client.delete("/api/v1/projects/99999")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_project_no_permission(self, client: AsyncClient, db_session):
        """测试删除项目失败 - 无权限"""
        from app.models import User, Project
        from app.auth import get_password_hash
        owner = User(
            email="owner2@example.com",
            username="owner2",
            hashed_password=get_password_hash("password123"),
            first_name="Owner",
            last_name="User",
            is_active=True
        )
        other_user = User(
            email="other2@example.com",
            username="otheruser2",
            hashed_password=get_password_hash("password123"),
            first_name="Other",
            last_name="User",
            is_active=True
        )
        db_session.add_all([owner, other_user])
        db_session.commit()
        
        project = Project(
            name="Owner's Project",
            status=ProjectStatus.ACTIVE,
            owner_id=owner.id
        )
        db_session.add(project)
        db_session.commit()
        
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "otheruser2", "password": "password123"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
        
        response = await client.delete(f"/api/v1/projects/{project.id}")
        
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_add_member_success(self, authenticated_client: AsyncClient, test_project, db_session, test_user):
        """测试添加项目成员成功"""
        from app.models import User
        new_member = User(
            email="newmember@example.com",
            username="newmember",
            hashed_password="hash",
            first_name="New",
            last_name="Member",
            is_active=True
        )
        db_session.add(new_member)
        db_session.commit()
        
        response = await authenticated_client.post(
            f"/api/v1/projects/{test_project.id}/members/{new_member.id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        member_ids = [m["id"] for m in data["members"]]
        assert new_member.id in member_ids

    @pytest.mark.asyncio
    async def test_add_member_already_exists(self, authenticated_client: AsyncClient, test_project, db_session):
        """测试添加项目成员失败 - 已存在"""
        from app.models import User
        member = User(
            email="existing@example.com",
            username="existing",
            hashed_password="hash",
            first_name="Existing",
            last_name="Member",
            is_active=True
        )
        db_session.add(member)
        db_session.commit()
        
        test_project.members.append(member)
        db_session.commit()
        
        response = await authenticated_client.post(
            f"/api/v1/projects/{test_project.id}/members/{member.id}"
        )
        
        assert response.status_code == 400
        assert response.json()["detail"] == "User is already a member of this project"

    @pytest.mark.asyncio
    async def test_remove_member_success(self, authenticated_client: AsyncClient, test_project, db_session):
        """测试移除项目成员成功"""
        from app.models import User
        member = User(
            email="remove@example.com",
            username="removeme",
            hashed_password="hash",
            first_name="Remove",
            last_name="Me",
            is_active=True
        )
        db_session.add(member)
        db_session.commit()
        
        test_project.members.append(member)
        db_session.commit()
        
        response = await authenticated_client.delete(
            f"/api/v1/projects/{test_project.id}/members/{member.id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        member_ids = [m["id"] for m in data["members"]]
        assert member.id not in member_ids

    @pytest.mark.asyncio
    async def test_remove_member_not_found(self, authenticated_client: AsyncClient, test_project):
        """测试移除项目成员失败 - 不存在"""
        response = await authenticated_client.delete(
            f"/api/v1/projects/{test_project.id}/members/99999"
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_admin_can_access_all_projects(self, admin_client: AsyncClient, db_session):
        """测试管理员可以访问所有项目"""
        from app.models import User, Project
        other_user = User(
            email="someone@example.com",
            username="someone",
            hashed_password="hash",
            first_name="Some",
            last_name="One",
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()
        
        for i in range(3):
            project = Project(
                name=f"Other User Project {i}",
                status=ProjectStatus.ACTIVE,
                owner_id=other_user.id
            )
            db_session.add(project)
        db_session.commit()
        
        response = await admin_client.get("/api/v1/projects")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
