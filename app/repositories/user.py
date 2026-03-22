import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_user_by_username(self, username: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
        # result.scalars().all()        # → [User, User, User]  全部 model 物件
        # result.scalars().first()      # → User                第一筆
        # result.scalar_one_or_none()   # → User | None         單筆
        # result.all()                  # → [(User,), (User,)]  tuple 格式
        # result.mappings().all()       # → [{"id": 1, ...}]    dict 格式

    async def create_user(self, user: User) -> User:
        # password 在 service/router 層 hash
        self.session.add(user)
        await self.session.commit()

        # commit 之後，DB 可能會自動產生一些值（如 id、created_at），
        # 但 Python 物件裡還不知道這些值，
        # refresh 就是重新從 DB 把最新狀態同步回來
        await self.session.refresh(user)
        return user
