"""
Pydantic Schemas 单元测试
测试所有Pydantic模型的验证逻辑和序列化
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app import schemas
from app.models import UserRole, ProjectStatus, TaskStatus, TaskPriority, NotificationType


class TestTokenSchemas:
    """Token相关Schema测试"""

    def test_token_create(self):
        """
        测试场景：正常创建Token
        验证：Token对象正确创建
        """
        token = schemas.Token(
            access_token="test_access_token",
            refresh_token="test_refresh_token"
        )
        assert token.access_token == "test_access_token"
        assert token.refresh_token == "test_refresh_token"
        assert token.token_type == "bearer"

    def test_token_with_custom_type(self):
        """
        测试场景：创建自定义token_type的Token
        验证：token_type被正确设置
        """
        token = schemas.Token(
            access_token="test",
            refresh_token="test",
            token_type="custom"
        )
        assert token.token_type == "custom"

    def test_token_payload(self):
        """
        测试场景：创建TokenPayload
        验证：payload包含正确的sub和exp
        """
        now = datetime.utcnow()
        payload = schemas.TokenPayload(sub=1, exp=now)
        assert payload.sub == 1
        assert payload.exp == now

    def test_token_payload_optional(self):
        """
        测试场景：创建空的TokenPayload
        验证：可选字段可以为None
        """
        payload = schemas.TokenPayload()
        assert payload.sub is None
        assert payload.exp is None


class TestUserSchemas:
    """用户相关Schema测试"""

    def test_user_create_valid(self):
        """
        测试场景：正常创建用户
        验证：用户对象正确创建
        """
        user = schemas.UserCreate(
            email="test@example.com",
            username="testuser",
            password="password123",
            first_name="Test",
            last_name="User",
            role=UserRole.MEMBER
        )
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.role == UserRole.MEMBER

    def test_user_create_default_role(self):
        """
        测试场景：创建用户时不指定角色
        验证：默认角色为MEMBER
        """
        user = schemas.UserCreate(
            email="test@example.com",
            username="testuser",
            password="password123",
            first_name="Test",
            last_name="User"
        )
        assert user.role == UserRole.MEMBER

    def test_user_create_invalid_email(self):
        """
        测试场景：创建用户时使用无效邮箱
        验证：抛出ValidationError
        """
        with pytest.raises(ValidationError) as exc_info:
            schemas.UserCreate(
                email="invalid_email",
                username="testuser",
                password="password123",
                first_name="Test",
                last_name="User"
            )
        assert "email" in str(exc_info.value)

    def test_user_create_short_password(self):
        """
        测试场景：创建用户时密码太短
        验证：抛出ValidationError
        """
        with pytest.raises(ValidationError) as exc_info:
            schemas.UserCreate(
                email="test@example.com",
                username="testuser",
                password="short",
                first_name="Test",
                last_name="User"
            )
        assert "password" in str(exc_info.value)

    def test_user_login(self):
        """
        测试场景：正常创建登录请求
        验证：登录对象正确创建
        """
        login = schemas.UserLogin(
            username="testuser",
            password="password123"
        )
        assert login.username == "testuser"
        assert login.password == "password123"

    def test_user_update_partial(self):
        """
        测试场景：部分更新用户信息
        验证：只更新指定字段
        """
        update = schemas.UserUpdate(
            first_name="New Name"
        )
        assert update.first_name == "New Name"
        assert update.email is None
        assert update.last_name is None

    def test_user_update_invalid_email(self):
        """
        测试场景：更新用户时使用无效邮箱
        验证：抛出ValidationError
        """
        with pytest.raises(ValidationError) as exc_info:
            schemas.UserUpdate(email="invalid_email")
        assert "email" in str(exc_info.value)

    def test_user_response(self):
        """
        测试场景：创建用户响应对象
        验证：响应包含所有必需字段
        """
        now = datetime.utcnow()
        user = schemas.UserResponse(
            id=1,
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            role=UserRole.MEMBER,
            is_active=True,
            created_at=now
        )
        assert user.id == 1
        assert user.is_active is True
        assert user.created_at == now


class TestProjectSchemas:
    """项目相关Schema测试"""

    def test_project_create_valid(self):
        """
        测试场景：正常创建项目
        验证：项目对象正确创建
        """
        project = schemas.ProjectCreate(
            name="Test Project",
            description="Test Description",
            status=ProjectStatus.PLANNING,
            budget=10000.0,
            member_ids=[1, 2, 3]
        )
        assert project.name == "Test Project"
        assert project.budget == 10000.0
        assert project.member_ids == [1, 2, 3]

    def test_project_create_default_status(self):
        """
        测试场景：创建项目时不指定状态
        验证：默认状态为PLANNING
        """
        project = schemas.ProjectCreate(
            name="Test Project"
        )
        assert project.status == ProjectStatus.PLANNING
        assert project.member_ids == []

    def test_project_create_empty_name(self):
        """
        测试场景：创建项目时名称为空
        验证：抛出ValidationError
        """
        with pytest.raises(ValidationError) as exc_info:
            schemas.ProjectCreate(name="")
        assert "name" in str(exc_info.value)

    def test_project_create_negative_budget(self):
        """
        测试场景：创建项目时预算为负数
        验证：抛出ValidationError
        """
        with pytest.raises(ValidationError) as exc_info:
            schemas.ProjectCreate(
                name="Test Project",
                budget=-100
            )
        assert "budget" in str(exc_info.value)

    def test_project_update_partial(self):
        """
        测试场景：部分更新项目信息
        验证：只更新指定字段
        """
        update = schemas.ProjectUpdate(
            description="Updated Description"
        )
        assert update.description == "Updated Description"
        assert update.name is None

    def test_project_update_invalid_name(self):
        """
        测试场景：更新项目时名称为空
        验证：抛出ValidationError
        """
        with pytest.raises(ValidationError) as exc_info:
            schemas.ProjectUpdate(name="")
        assert "name" in str(exc_info.value)


class TestTaskSchemas:
    """任务相关Schema测试"""

    def test_task_create_valid(self):
        """
        测试场景：正常创建任务
        验证：任务对象正确创建
        """
        task = schemas.TaskCreate(
            title="Test Task",
            description="Test Description",
            project_id=1,
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            estimated_hours=8.0,
            assignee_id=2
        )
        assert task.title == "Test Task"
        assert task.project_id == 1
        assert task.priority == TaskPriority.HIGH

    def test_task_create_default_status(self):
        """
        测试场景：创建任务时不指定状态
        验证：默认状态为TODO
        """
        task = schemas.TaskCreate(
            title="Test Task",
            project_id=1
        )
        assert task.status == TaskStatus.TODO
        assert task.priority == TaskPriority.MEDIUM

    def test_task_create_with_dependencies(self):
        """
        测试场景：创建任务时包含依赖
        验证：依赖被正确设置
        """
        task = schemas.TaskCreate(
            title="Test Task",
            project_id=1,
            dependencies=[
                schemas.TaskDependencyCreate(
                    depends_on_task_id=1,
                    dependency_type="finish_to_start"
                )
            ]
        )
        assert len(task.dependencies) == 1
        assert task.dependencies[0].depends_on_task_id == 1

    def test_task_create_empty_title(self):
        """
        测试场景：创建任务时标题为空
        验证：抛出ValidationError
        """
        with pytest.raises(ValidationError) as exc_info:
            schemas.TaskCreate(title="", project_id=1)
        assert "title" in str(exc_info.value)

    def test_task_create_negative_hours(self):
        """
        测试场景：创建任务时预估工时为负数
        验证：抛出ValidationError
        """
        with pytest.raises(ValidationError) as exc_info:
            schemas.TaskCreate(
                title="Test Task",
                project_id=1,
                estimated_hours=-5
            )
        assert "estimated_hours" in str(exc_info.value)

    def test_task_update_partial(self):
        """
        测试场景：部分更新任务信息
        验证：只更新指定字段
        """
        update = schemas.TaskUpdate(
            status=TaskStatus.IN_PROGRESS
        )
        assert update.status == TaskStatus.IN_PROGRESS
        assert update.title is None

    def test_task_dependency_create(self):
        """
        测试场景：创建任务依赖
        验证：依赖对象正确创建
        """
        dep = schemas.TaskDependencyCreate(
            depends_on_task_id=1,
            dependency_type="start_to_start"
        )
        assert dep.depends_on_task_id == 1
        assert dep.dependency_type == "start_to_start"

    def test_task_dependency_default_type(self):
        """
        测试场景：创建任务依赖时不指定类型
        验证：默认类型为finish_to_start
        """
        dep = schemas.TaskDependencyCreate(depends_on_task_id=1)
        assert dep.dependency_type == "finish_to_start"


class TestTimeEntrySchemas:
    """工时记录相关Schema测试"""

    def test_time_entry_create_valid(self):
        """
        测试场景：正常创建工时记录
        验证：工时记录对象正确创建
        """
        entry = schemas.TimeEntryCreate(
            task_id=1,
            hours=8.0,
            date="2024-01-15",
            description="Worked on task"
        )
        assert entry.task_id == 1
        assert entry.hours == 8.0
        assert entry.date == "2024-01-15"

    def test_time_entry_create_zero_hours(self):
        """
        测试场景：创建工时记录时工时为0
        验证：抛出ValidationError
        """
        with pytest.raises(ValidationError) as exc_info:
            schemas.TimeEntryCreate(
                task_id=1,
                hours=0,
                date="2024-01-15"
            )
        assert "hours" in str(exc_info.value)

    def test_time_entry_create_negative_hours(self):
        """
        测试场景：创建工时记录时工时为负数
        验证：抛出ValidationError
        """
        with pytest.raises(ValidationError) as exc_info:
            schemas.TimeEntryCreate(
                task_id=1,
                hours=-5,
                date="2024-01-15"
            )
        assert "hours" in str(exc_info.value)

    def test_time_entry_update_partial(self):
        """
        测试场景：部分更新工时记录
        验证：只更新指定字段
        """
        update = schemas.TimeEntryUpdate(
            description="Updated description"
        )
        assert update.description == "Updated description"
        assert update.hours is None

    def test_time_entry_update_invalid_hours(self):
        """
        测试场景：更新工时记录时工时为0
        验证：抛出ValidationError
        """
        with pytest.raises(ValidationError) as exc_info:
            schemas.TimeEntryUpdate(hours=0)
        assert "hours" in str(exc_info.value)


class TestDocumentSchemas:
    """文档相关Schema测试"""

    def test_document_create_valid(self):
        """
        测试场景：正常创建文档
        验证：文档对象正确创建
        """
        doc = schemas.DocumentCreate(
            name="test.pdf",
            project_id=1
        )
        assert doc.name == "test.pdf"
        assert doc.project_id == 1

    def test_document_response(self):
        """
        测试场景：创建文档响应对象
        验证：响应包含所有必需字段
        """
        now = datetime.utcnow()
        user = schemas.UserResponse(
            id=1,
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            role=UserRole.MEMBER,
            is_active=True,
            created_at=now
        )
        doc = schemas.DocumentResponse(
            id=1,
            name="test.pdf",
            project_id=1,
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=1,
            uploaded_by_user=user,
            version=1,
            created_at=now
        )
        assert doc.id == 1
        assert doc.uploaded_by_user.username == "testuser"


class TestNotificationSchemas:
    """通知相关Schema测试"""

    def test_notification_create_valid(self):
        """
        测试场景：正常创建通知
        验证：通知对象正确创建
        """
        notif = schemas.NotificationCreate(
            user_id=1,
            type=NotificationType.TASK_ASSIGNED,
            title="New Task",
            message="You have been assigned a new task",
            related_project_id=1,
            related_task_id=2
        )
        assert notif.user_id == 1
        assert notif.type == NotificationType.TASK_ASSIGNED
        assert notif.related_project_id == 1

    def test_notification_response(self):
        """
        测试场景：创建通知响应对象
        验证：响应包含所有必需字段
        """
        now = datetime.utcnow()
        notif = schemas.NotificationResponse(
            id=1,
            user_id=1,
            type=NotificationType.PROJECT_UPDATE,
            title="Project Updated",
            message="A project has been updated",
            is_read=False,
            created_at=now
        )
        assert notif.id == 1
        assert notif.is_read is False


class TestStatisticsSchemas:
    """统计相关Schema测试"""

    def test_project_statistics(self):
        """
        测试场景：创建项目统计对象
        验证：统计对象正确创建
        """
        stats = schemas.ProjectStatistics(
            total_projects=10,
            active_projects=5,
            completed_projects=3,
            total_tasks=50,
            completed_tasks=20,
            in_progress_tasks=15,
            overdue_tasks=5
        )
        assert stats.total_projects == 10
        assert stats.completed_tasks == 20

    def test_user_statistics(self):
        """
        测试场景：创建用户统计对象
        验证：统计对象正确创建
        """
        stats = schemas.UserStatistics(
            user_id=1,
            total_tasks=20,
            completed_tasks=10,
            in_progress_tasks=5,
            total_hours_logged=80.5,
            projects_count=3
        )
        assert stats.user_id == 1
        assert stats.total_hours_logged == 80.5

    def test_time_report_entry(self):
        """
        测试场景：创建工时报告条目
        验证：条目正确创建
        """
        now = datetime.utcnow()
        entry = schemas.TimeReportEntry(
            date=now,
            hours=8.0,
            task_count=3
        )
        assert entry.hours == 8.0
        assert entry.task_count == 3

    def test_paginated_response(self):
        """
        测试场景：创建分页响应
        验证：分页信息正确
        """
        response = schemas.PaginatedResponse(
            items=[{"id": 1}, {"id": 2}],
            total=10,
            page=1,
            page_size=2,
            total_pages=5
        )
        assert response.total == 10
        assert response.page == 1
        assert response.total_pages == 5


class TestMilestoneSchemas:
    """里程碑相关Schema测试"""

    def test_milestone_create_valid(self):
        """
        测试场景：正常创建里程碑
        验证：里程碑对象正确创建
        """
        due_date = datetime.utcnow()
        milestone = schemas.MilestoneCreate(
            name="v1.0 Release",
            description="First major release",
            due_date=due_date
        )
        assert milestone.name == "v1.0 Release"
        assert milestone.due_date == due_date

    def test_milestone_create_empty_name(self):
        """
        测试场景：创建里程碑时名称为空
        验证：抛出ValidationError
        """
        with pytest.raises(ValidationError) as exc_info:
            schemas.MilestoneCreate(
                name="",
                due_date=datetime.utcnow()
            )
        assert "name" in str(exc_info.value)

    def test_milestone_response(self):
        """
        测试场景：创建里程碑响应对象
        验证：响应包含所有必需字段
        """
        now = datetime.utcnow()
        milestone = schemas.MilestoneResponse(
            id=1,
            name="v1.0",
            description="Release",
            due_date=now,
            project_id=1,
            completed_at=None,
            created_at=now
        )
        assert milestone.id == 1
        assert milestone.project_id == 1


class TestProjectMemberSchema:
    """项目成员Schema测试"""

    def test_project_member(self):
        """
        测试场景：创建项目成员对象
        验证：成员对象正确创建
        """
        now = datetime.utcnow()
        member = schemas.ProjectMember(
            id=1,
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            role="member",
            joined_at=now
        )
        assert member.id == 1
        assert member.role == "member"
        assert member.joined_at == now
