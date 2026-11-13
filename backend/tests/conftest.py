import asyncio
import uuid
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from backend.app.config import settings
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.user import User
from backend.app.services.auth_service import create_access_token, get_password_hash

# Use in-memory SQLite for high-speed, isolated async test execution
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


import backend.app.database as db_module


@pytest_asyncio.fixture(scope="function", autouse=True)
def override_db_session_factory():
    orig_factory = db_module.AsyncSessionLocal
    db_module.AsyncSessionLocal = TestAsyncSessionLocal
    yield
    db_module.AsyncSessionLocal = orig_factory


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestAsyncSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        email="engineer@rayhan-ai.com",
        username="rayhan_engineer",
        hashed_password=get_password_hash("SecurePass123!"),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
def auth_headers(test_user: User) -> dict:
    token, _ = create_access_token(
        data={"sub": str(test_user.id), "email": test_user.email, "username": test_user.username}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
async def other_user(db_session: AsyncSession) -> User:
    user = User(
        email="other@rayhan-ai.com",
        username="other_dev",
        hashed_password=get_password_hash("OtherPass456!"),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
def other_auth_headers(other_user: User) -> dict:
    token, _ = create_access_token(
        data={"sub": str(other_user.id), "email": other_user.email, "username": other_user.username}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
async def superuser(db_session: AsyncSession) -> User:
    user = User(
        email="admin@rayhan-ai.com",
        username="super_rayhan",
        hashed_password=get_password_hash("SuperSecurePass789!"),
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
def super_auth_headers(superuser: User) -> dict:
    token, _ = create_access_token(
        data={"sub": str(superuser.id), "email": superuser.email, "username": superuser.username}
    )
    return {"Authorization": f"Bearer {token}"}
