import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.auth import get_password_hash
from app.models import User, UserRole, Project, ProjectStatus, Task

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_user(db_session):
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


@pytest.fixture(scope="function")
def test_admin_user(db_session):
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


@pytest.fixture(scope="function")
def test_project_manager(db_session):
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


@pytest.fixture(scope="function")
def test_project(db_session, test_user):
    project = Project(
        name="Test Project",
        description="Test Description",
        status=ProjectStatus.ACTIVE,
        owner_id=test_user.id,
        budget=10000.0
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    project.members.append(test_user)
    db_session.commit()
    return project


@pytest.fixture(scope="function")
def test_task(db_session, test_project, test_user):
    task = Task(
        title="Test Task",
        description="Test Task Description",
        status="in_progress",
        priority="medium",
        project_id=test_project.id,
        assignee_id=test_user.id,
        created_by=test_user.id,
        estimated_hours=8,
        actual_hours=0
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


@pytest_asyncio.fixture(scope="function")
async def client():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(client, test_user):
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "password123"}
    )
    tokens = response.json()
    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"
    return client


@pytest_asyncio.fixture(scope="function")
async def admin_client(client, test_admin_user):
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    tokens = response.json()
    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"
    return client


@pytest_asyncio.fixture(scope="function")
async def pm_client(client, test_project_manager):
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "projectmanager", "password": "pm123"}
    )
    tokens = response.json()
    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"
    return client


@pytest_asyncio.fixture(scope="function")
async def user_auth_headers(client, test_user):
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "password123"}
    )
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest_asyncio.fixture(scope="function")
async def admin_auth_headers(client, test_admin_user):
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture(scope="function")
def admin_user(test_admin_user):
    return test_admin_user
