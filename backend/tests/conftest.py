import sys
from pathlib import Path
import pytest
import pytest_asyncio
import asyncio
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app
from app.database import Base, get_db
from app.models import User, UserRole, Project, ProjectStatus, Task, TaskStatus, TaskPriority, TimeEntry, Document
from app.auth import get_password_hash, create_access_token

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    admin = User(
        email="admin@example.com",
        username="adminuser",
        hashed_password=get_password_hash("admin123"),
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin)
    
    test_user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("password123"),
        first_name="Test",
        last_name="User",
        role=UserRole.MEMBER,
        is_active=True,
    )
    db.add(test_user)
    
    pm = User(
        email="pm@example.com",
        username="pmuser",
        hashed_password=get_password_hash("pm123"),
        first_name="Project",
        last_name="Manager",
        role=UserRole.PROJECT_MANAGER,
        is_active=True,
    )
    db.add(pm)
    db.commit()
    
    db.refresh(admin)
    db.refresh(test_user)
    db.refresh(pm)
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        ac._admin_user = admin
        ac._test_user = test_user
        ac._pm_user = pm
        ac._db = db
        yield ac
    
    app.dependency_overrides.clear()
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db: Session) -> User:
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("password123"),
        first_name="Test",
        last_name="User",
        role=UserRole.MEMBER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db: Session) -> User:
    user = User(
        email="admin@example.com",
        username="adminuser",
        hashed_password=get_password_hash("admin123"),
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def project_manager_user(db: Session) -> User:
    user = User(
        email="pm@example.com",
        username="pmuser",
        hashed_password=get_password_hash("pm123"),
        first_name="Project",
        last_name="Manager",
        role=UserRole.PROJECT_MANAGER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_project(db: Session, test_user: User) -> Project:
    project = Project(
        name="Test Project",
        description="Test project description",
        status=ProjectStatus.ACTIVE,
        owner_id=test_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@pytest.fixture
def test_task(db: Session, test_project: Project, test_user: User) -> Task:
    task = Task(
        project_id=test_project.id,
        title="Test Task",
        description="Test task description",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        created_by=test_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@pytest.fixture
def test_time_entry(db: Session, test_task: Task, test_user: User) -> TimeEntry:
    from datetime import datetime
    entry = TimeEntry(
        task_id=test_task.id,
        user_id=test_user.id,
        description="Test time entry",
        hours=2.5,
        date=datetime.utcnow(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    token = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(admin_user: User) -> dict:
    token = create_access_token(subject=admin_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def pm_auth_headers(project_manager_user: User) -> dict:
    token = create_access_token(subject=project_manager_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def async_auth_headers(async_client: AsyncClient) -> dict:
    test_user = async_client._test_user
    token = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def async_admin_auth_headers(async_client: AsyncClient) -> dict:
    admin_user = async_client._admin_user
    token = create_access_token(subject=admin_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def async_pm_auth_headers(async_client: AsyncClient) -> dict:
    pm_user = async_client._pm_user
    token = create_access_token(subject=pm_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def async_test_user(async_client: AsyncClient) -> User:
    return async_client._test_user


@pytest.fixture
def async_admin_user(async_client: AsyncClient) -> User:
    return async_client._admin_user
