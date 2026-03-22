from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import create_access_token, create_refresh_token
from ..models.user import User
from ..repositories.user import UserRepository
from ..schemas.user import TokenResponse

# 嚴格來說，HTTPException 不應該出現在 service / repository 層
# 原因：HTTPException 是 HTTP 的概念，但 service 和 repository 是業務邏輯層
# 但本project為練習專案，且規模小，為求方便，不再自定義exception


class AuthServices:
    def __init__(self, session: AsyncSession):  # session: 跟 db 的連線
        self.user_repository = UserRepository(session)

    async def register(self, username: str, password: str) -> TokenResponse:
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

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def login(self, username: str, password: str) -> TokenResponse:
        user = await self.user_repository.get_user_by_username(username=username)
        if not user or not user.verify_password(password=password):
            raise HTTPException(status_code=401, detail="Invalid Credentials")
        access_token = create_access_token(user_id=user.id)
        refresh_token = create_refresh_token(user_id=user.id)

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
