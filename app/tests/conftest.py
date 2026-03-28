import os
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base
from app.db.redis import get_redis as app_get_redis
from app.db.session import get_db as app_get_db
from app.main import app
from app.models.task import Task
from app.models.user import User

TEST_SQLALCHEMY_DATABASE_URL = os.environ.get(
    "TEST_SQLALCHEMY_DATABASE_URL",
    "postgresql+asyncpg://admin:admin@localhost:5432/testdb",
)
TEST_REDIS_DATABASE_URL = os.environ.get(
    "TEST_REDIS_DATABASE_URL", "redis://localhost:6379/1"
)


# session scope:
# 整個 pytest 執行期間只建立一次，所有測試共用同一個實例
@pytest_asyncio.fixture(scope="function")
async def engine() -> AsyncGenerator[AsyncEngine]:
    engine = create_async_engine(TEST_SQLALCHEMY_DATABASE_URL)

    # engine.begin()
    #     ├── 1. 從 connection pool 取出一條連線 (conn)
    #     ├── 2. 自動開始一個 transaction (BEGIN)
    #     └── 3. 結束時：
    #             ├── 成功 → 自動 COMMIT
    #             └── 例外 → 自動 ROLLBACK
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # create all tables

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # clear all when ending tests

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def get_db(engine) -> AsyncGenerator[AsyncSession]:
    AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)

    async with AsyncSessionFactory() as session:
        try:
            yield session
        finally:
            await session.execute(delete(Task))  # Task有FK,先刪
            await session.execute(delete(User))
            await session.commit()


@pytest_asyncio.fixture(scope="function")
async def get_redis() -> AsyncGenerator[Redis]:
    async with Redis.from_url(TEST_REDIS_DATABASE_URL, decode_responses=True) as redis:
        yield redis
        await redis.flushdb()


@pytest_asyncio.fixture(scope="function")
async def client(get_db, get_redis) -> AsyncGenerator[AsyncClient]:
    # FastAPI 內建的功能，專門用來在測試時替換依賴注入
    # dependency_overrides 期望的是一個callable（可被呼叫的函數），不是直接的值
    app.dependency_overrides[app_get_db] = lambda: get_db
    app.dependency_overrides[app_get_redis] = lambda: get_redis

    # 一般情況：
    # 測試 → (真實網路) → http://localhost:8000 → FastAPI

    # 測試時：
    # 測試 → AsyncClient → ASGITransport → FastAPI app（直接在記憶體內呼叫）
    #                                            ↑ 不需要啟動伺服器
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def registered_user(client) -> dict:
    payload = {"username": "test_user", "password": "test_password"}

    response = await client.post("/auth/register", json=payload)
    data = response.json()

    # get_db fixture 已經負責清除 DB 了，所以用 return 就夠了
    # 不用 yield
    return {
        "username": payload["username"],
        "password": payload["password"],
        "access_token": data["access_token"],
        "refresh_token": response.cookies.get("refresh_token"),
    }


@pytest_asyncio.fixture(scope="function")
async def created_task(client, registered_user) -> dict:
    headers = {"Authorization": f"Bearer {registered_user['access_token']}"}
    task = {"title": "test_title", "description": "test_description"}
    res = await client.post("/tasks/", headers=headers, json=task)

    return res.json()
