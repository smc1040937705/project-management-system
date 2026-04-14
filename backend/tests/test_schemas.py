import pytest
from pydantic import ValidationError
from app.schemas import (
    UserCreate, UserUpdate, UserResponse,
    ProjectCreate, ProjectUpdate, ProjectResponse,
    TaskCreate, TaskUpdate, TaskResponse,
    TimeEntryCreate, TimeEntryUpdate,
    DocumentCreate, DocumentResponse,
    TaskDependencyCreate, TaskDependencyResponse,
    NotificationCreate, NotificationResponse,
    Token, TokenPayload
)
from app.models import UserRole, ProjectStatus, TaskStatus, TaskPriority, NotificationType
from datetime import datetime


class TestUserSchemas:
    def test_user_create_valid(self):
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="password123",
            first_name="Test",
            last_name="User",
            role=UserRole.MEMBER
        )
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.password == "password123"

    def test_user_create_default_role(self):
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="password123",
            first_name="Test",
            last_name="User"
        )
        assert user.role == UserRole.MEMBER

    def test_user_create_short_password(self):
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="short",
                first_name="Test",
                last_name="User"
            )
        assert "at least 8 characters" in str(exc_info.value).lower() or "min_length" in str(exc_info.value).lower()

    def test_user_create_invalid_email(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid-email",
                username="testuser",
                password="password123",
                first_name="Test",
                last_name="User"
            )

    def test_user_update_partial(self):
        update = UserUpdate(first_name="Updated")
        assert update.first_name == "Updated"
        assert update.email is None
        assert update.role is None

    def test_user_update_all_fields(self):
        update = UserUpdate(
            email="updated@example.com",
            first_name="Updated",
            last_name="Name",
            role=UserRole.ADMIN,
            is_active=False,
            avatar_url="https://example.com/avatar.png"
        )
        assert update.email == "updated@example.com"
        assert update.first_name == "Updated"
        assert update.role == UserRole.ADMIN
        assert update.is_active is False


class TestProjectSchemas:
    def test_project_create_valid(self):
        project = ProjectCreate(
            name="Test Project",
            description="A test project",
            status=ProjectStatus.ACTIVE
        )
        assert project.name == "Test Project"
        assert project.status == ProjectStatus.ACTIVE

    def test_project_create_with_members(self):
        project = ProjectCreate(
            name="Test Project",
            member_ids=[1, 2, 3]
        )
        assert project.member_ids == [1, 2, 3]

    def test_project_create_empty_name(self):
        with pytest.raises(ValidationError):
            ProjectCreate(name="")

    def test_project_create_name_too_long(self):
        with pytest.raises(ValidationError):
            ProjectCreate(name="x" * 201)

    def test_project_create_negative_budget(self):
        with pytest.raises(ValidationError):
            ProjectCreate(name="Test", budget=-100)

    def test_project_update_partial(self):
        update = ProjectUpdate(name="Updated Name")
        assert update.name == "Updated Name"
        assert update.status is None


class TestTaskSchemas:
    def test_task_create_valid(self):
        task = TaskCreate(
            title="Test Task",
            project_id=1,
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH
        )
        assert task.title == "Test Task"
        assert task.project_id == 1
        assert task.status == TaskStatus.TODO

    def test_task_create_with_assignee(self):
        task = TaskCreate(
            title="Test Task",
            project_id=1,
            assignee_id=5
        )
        assert task.assignee_id == 5

    def test_task_create_empty_title(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="", project_id=1)

    def test_task_create_title_too_long(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="x" * 201, project_id=1)

    def test_task_create_negative_estimated_hours(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="Test", project_id=1, estimated_hours=-5)

    def test_task_update_partial(self):
        update = TaskUpdate(status=TaskStatus.DONE)
        assert update.status == TaskStatus.DONE
        assert update.title is None

    def test_task_update_all_fields(self):
        update = TaskUpdate(
            title="Updated Task",
            description="New description",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            assignee_id=10,
            estimated_hours=8.5,
            due_date="2024-12-31"
        )
        assert update.title == "Updated Task"
        assert update.status == TaskStatus.IN_PROGRESS
        assert update.estimated_hours == 8.5


class TestTaskDependencySchemas:
    def test_task_dependency_create_valid(self):
        dep = TaskDependencyCreate(depends_on_task_id=5)
        assert dep.depends_on_task_id == 5
        assert dep.dependency_type == "finish_to_start"

    def test_task_dependency_create_custom_type(self):
        dep = TaskDependencyCreate(
            depends_on_task_id=5,
            dependency_type="start_to_start"
        )
        assert dep.dependency_type == "start_to_start"


class TestTimeEntrySchemas:
    def test_time_entry_create_valid(self):
        entry = TimeEntryCreate(
            task_id=1,
            hours=2.5,
            date="2024-01-15"
        )
        assert entry.task_id == 1
        assert entry.hours == 2.5

    def test_time_entry_create_zero_hours(self):
        with pytest.raises(ValidationError):
            TimeEntryCreate(task_id=1, hours=0, date="2024-01-15")

    def test_time_entry_create_negative_hours(self):
        with pytest.raises(ValidationError):
            TimeEntryCreate(task_id=1, hours=-1, date="2024-01-15")

    def test_time_entry_update_partial(self):
        update = TimeEntryUpdate(hours=5.0)
        assert update.hours == 5.0
        assert update.description is None


class TestDocumentSchemas:
    def test_document_create_valid(self):
        doc = DocumentCreate(name="test.pdf", project_id=1)
        assert doc.name == "test.pdf"
        assert doc.project_id == 1


class TestNotificationSchemas:
    def test_notification_create_valid(self):
        notif = NotificationCreate(
            type=NotificationType.TASK_ASSIGNED,
            title="New Task",
            message="You have been assigned a new task",
            user_id=1
        )
        assert notif.type == NotificationType.TASK_ASSIGNED
        assert notif.title == "New Task"

    def test_notification_create_with_relations(self):
        notif = NotificationCreate(
            type=NotificationType.PROJECT_UPDATE,
            title="Project Updated",
            message="Project has been updated",
            user_id=1,
            related_project_id=5,
            related_task_id=10
        )
        assert notif.related_project_id == 5
        assert notif.related_task_id == 10


class TestTokenSchemas:
    def test_token_valid(self):
        token = Token(
            access_token="access_token_value",
            refresh_token="refresh_token_value"
        )
        assert token.access_token == "access_token_value"
        assert token.refresh_token == "refresh_token_value"
        assert token.token_type == "bearer"

    def test_token_payload_valid(self):
        payload = TokenPayload(sub=1, exp=datetime.utcnow())
        assert payload.sub == 1
        assert payload.exp is not None

    def test_token_payload_optional(self):
        payload = TokenPayload()
        assert payload.sub is None
        assert payload.exp is None
