import time
import uuid
from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Depends, HTTPException, Request
from redis.asyncio import Redis

from ..db.redis import get_redis

type RateLimiter = Callable[..., Coroutine[Any, Any, None]]


# fixed window
def make_rate_limiter(name: str, limit: int, window: int) -> RateLimiter:
    async def _rate_limiter(req: Request, redis: Redis = Depends(get_redis)) -> None:
        # test環境中，req.client某些環境下可能為None 因此加上 "unknown" 避免 None
        ip = req.client.host if req.client else "unknown"
        key = f"rate_limit:{name}:{ip}"

        # key 不存在 → incr 當作 0 開始 → 回傳 1
        # key 存在   → 直接 +1 → 回傳新值
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window)

        if count > limit:
            raise HTTPException(status_code=429, detail="Too many requests")

    return _rate_limiter


def make_sliding_window_limiter(name: str, limit: int, window: int) -> RateLimiter:
    async def _rate_limiter(req: Request, redis: Redis = Depends(get_redis)) -> None:
        ip = req.client.host if req.client else "unknown"
        key = f"rate_limit:{name}:{ip}"

        now = time.time()
        window_start = now - window
        # 刪掉 window 之外的舊資料
        await redis.zremrangebyscore(key, "-inf", window_start)
        # time.time() 單位是秒
        count = await redis.zcount(key, window_start, now)

        # 先count再add的 所以當count == limit 時
        # 這次req就是第 limit+1 次
        if count >= limit:
            raise HTTPException(status_code=429, detail="Too many requests")
        await redis.zadd(key, {str(uuid.uuid4()): now})

        # 設TTL讓key自動過期
        await redis.expire(key, window)

    return _rate_limiter
