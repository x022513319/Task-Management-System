from collections.abc import AsyncGenerator

from redis.asyncio import ConnectionPool, Redis

from ..core.config import settings

pool: ConnectionPool | None = None


async def init_redis_pool():
    global pool
    pool = ConnectionPool.from_url(  # ← 賦值
        str(settings.REDIS_DATABASE_URL), max_connections=10, decode_responses=True
    )


async def close_redis_pool():
    global pool
    if pool:
        await pool.disconnect()


async def get_redis() -> AsyncGenerator[Redis]:
    # 只是讀取就不需要宣告 global
    async with Redis(connection_pool=pool) as redis:
        yield redis  # ← 把 redis 物件交給 FastAPI endpoint 使用


# yield = 暫停點，yield value = 暫停點 + 順便交出一個值

# async def endpoint(redis: Redis = Depends(get_redis)):
#     #                ↑ 接住 yield 出來的 redis 物件
#     await redis.get("key")

# Generator function — yield 多個值，可以暫停/繼續
# def generator():
#     yield 1
#     yield 2
#     yield 3

# AsyncGenerator
# 第一個 Redis — 這個 generator 會 yield 出 Redis 物件
# 第二個 None — send() 進去的型別，一般不用，固定寫 None
