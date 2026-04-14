import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, get_db
from app.main import app
from app.models import User, Project, Task, TimeEntry, Document, UserRole, ProjectStatus, TaskStatus, TaskPriority
from app.auth import get_password_hash, create_access_token


# 使用内存SQLite数据库进行测试
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    测试场景：为每个测试函数创建新的数据库会话
    验证：数据库在每次测试后都被清理
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session):
    """
    测试场景：创建测试客户端，使用内存数据库
    验证：API请求不会污染真实数据
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: Session):
    """
    测试场景：创建异步测试客户端
    验证：支持异步API测试
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session):
    """
    测试场景：创建普通测试用户
    验证：用户数据正确创建
    """
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("password123"),
        first_name="Test",
        last_name="User",
        role=UserRole.MEMBER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin(db_session: Session):
    """
    测试场景：创建管理员测试用户
    验证：管理员数据正确创建
    """
    admin = User(
        email="admin@example.com",
        username="admin",
        hashed_password=get_password_hash("admin123"),
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def test_project_manager(db_session: Session):
    """
    测试场景：创建项目经理测试用户
    验证：项目经理数据正确创建
    """
    pm = User(
        email="pm@example.com",
        username="projectmanager",
        hashed_password=get_password_hash("pm123"),
        first_name="Project",
        last_name="Manager",
        role=UserRole.PROJECT_MANAGER,
        is_active=True
    )
    db_session.add(pm)
    db_session.commit()
    db_session.refresh(pm)
    return pm


@pytest.fixture
def test_project(db_session: Session, test_user: User):
    """
    测试场景：创建测试项目
    验证：项目数据正确创建，所有者为test_user
    """
    project = Project(
        name="Test Project",
        description="Test Description",
        status=ProjectStatus.ACTIVE,
        owner_id=test_user.id
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_task(db_session: Session, test_project: Project, test_user: User):
    """
    测试场景：创建测试任务
    验证：任务数据正确创建，关联到测试项目
    """
    task = Task(
        project_id=test_project.id,
        title="Test Task",
        description="Test Task Description",
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
        created_by=test_user.id,
        assignee_id=test_user.id
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


@pytest.fixture
def test_time_entry(db_session: Session, test_task: Task, test_user: User):
    """
    测试场景：创建测试工时记录
    验证：工时记录数据正确创建
    """
    from datetime import datetime
    entry = TimeEntry(
        task_id=test_task.id,
        user_id=test_user.id,
        hours=8,
        date=datetime.utcnow(),
        description="Test work"
    )
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)
    return entry


@pytest.fixture
def user_token(test_user: User):
    """
    测试场景：生成普通用户认证token
    验证：token正确生成
    """
    return create_access_token(subject=test_user.id)


@pytest.fixture
def admin_token(test_admin: User):
    """
    测试场景：生成管理员认证token
    验证：token正确生成
    """
    return create_access_token(subject=test_admin.id)


@pytest.fixture
def pm_token(test_project_manager: User):
    """
    测试场景：生成项目经理认证token
    验证：token正确生成
    """
    return create_access_token(subject=test_project_manager.id)


@pytest.fixture
def auth_headers(user_token: str):
    """
    测试场景：生成普通用户认证头
    验证：认证头格式正确
    """
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_auth_headers(admin_token: str):
    """
    测试场景：生成管理员认证头
    验证：认证头格式正确
    """
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def pm_auth_headers(pm_token: str):
    """
    测试场景：生成项目经理认证头
    验证：认证头格式正确
    """
    return {"Authorization": f"Bearer {pm_token}"}
