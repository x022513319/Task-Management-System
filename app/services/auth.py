from fastapi import HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.security import create_access_token, create_refresh_token, verify_token
from ..models.user import User
from ..repositories.user import UserRepository

# 嚴格來說，HTTPException 不應該出現在 service / repository 層
# 原因：HTTPException 是 HTTP 的概念，但 service 和 repository 是業務邏輯層
# 但本project為練習專案，且規模小，為求方便，不再自定義exception


class AuthServices:
    def __init__(self, session: AsyncSession, redis: Redis):  # session: 跟 db 的連線
        self.redis = redis
        self.user_repository = UserRepository(session)

    async def register(self, username: str, password: str) -> tuple[str, str]:
        # User 是 SQLAlchemy model，不是 Pydantic model
        # 所以 password 可以空著
        # NOT NULL 檢查是在 session.commit() 的時候，由資料庫執行
        user = await self.user_repository.get_user_by_username(username=username)
        if user:
            # 實務上可以用模糊訊息來避免有心人嘗試探測 username 是否存在
            raise HTTPException(status_code=409, detail="Username already exists")
        user = User(username=username)
        user.set_password(password)
        user = await self.user_repository.create_user(user=user)
        access_token = create_access_token(user_id=user.id)
        refresh_token = create_refresh_token(user_id=user.id)
        await self.redis.set(
            f"refresh_token:{refresh_token}",  # key
            str(user.id),  # value
            ex=60
            * 60
            * 24
            * settings.REFRESH_TOKEN_EXPIRE_DAYS,  # TTL: measured in seconds
        )

        return access_token, refresh_token

    async def login(self, username: str, password: str) -> tuple[str, str]:
        user = await self.user_repository.get_user_by_username(username=username)
        if not user or not user.verify_password(password=password):
            raise HTTPException(status_code=401, detail="Invalid Credentials")
        access_token = create_access_token(user_id=user.id)
        refresh_token = create_refresh_token(user_id=user.id)
        await self.redis.set(
            f"refresh_token:{refresh_token}",  # key
            str(user.id),  # value
            ex=60
            * 60
            * 24
            * settings.REFRESH_TOKEN_EXPIRE_DAYS,  # TTL: measured in seconds
        )

        return access_token, refresh_token

    async def refresh(self, refresh_token: str) -> tuple[str, str]:
        payload = verify_token(token=refresh_token)  # 驗證, 解析 JWT 格式
        user_id = payload["sub"]

        # 檢查 Redis 存的 token 是否還有效
        key = f"refresh_token:{refresh_token}"
        stored = await self.redis.get(key)
        if not stored:
            raise HTTPException(status_code=401, detail="Token invalid")

        # 可以用 Redis 的 pipeline 來確保 Atomicity (此side project暫略)
        # Token Rotation
        await self.redis.delete(key)

        # create a new one
        new_access_token = create_access_token(user_id=user_id)
        new_refresh_token = create_refresh_token(user_id=user_id)

        await self.redis.set(
            f"refresh_token:{new_refresh_token}",  # key
            user_id,  # value
            ex=60
            * 60
            * 24
            * settings.REFRESH_TOKEN_EXPIRE_DAYS,  # TTL: measured in seconds
        )

        return new_access_token, new_refresh_token

    async def logout(self, refresh_token: str) -> None:
        key = f"refresh_token:{refresh_token}"
        stored = await self.redis.get(key)

        if not stored:
            raise HTTPException(status_code=401, detail="Token invalid")

        await self.redis.delete(key)
