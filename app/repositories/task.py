import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.task import Task
from ..schemas.task import TaskUpdate


class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # 找不到任何資料時回傳空 list [] 不需加 None
    async def get_tasks_by_user_id(self, user_id: uuid.UUID) -> list[Task]:
        result = await self.session.execute(
            select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc())
        )
        return list(result.scalars().all())
        # result.scalars().all()        # → [User, User, User]  全部 model 物件
        # result.scalars().first()      # → User                第一筆
        # result.scalar_one_or_none()   # → User | None         單筆
        # result.all()                  # → [(User,), (User,)]  tuple 格式
        # result.mappings().all()       # → [{"id": 1, ...}]    dict 格式

    async def get_task_by_id(
        self, task_id: uuid.UUID, user_id: uuid.UUID
    ) -> Task | None:
        result = await self.session.execute(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_task(
        self, user_id: uuid.UUID, title: str, description: str
    ) -> Task:
        task = Task(user_id=user_id, title=title, description=description)
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def update_task(self, task_id: uuid.UUID, data: TaskUpdate) -> Task | None:
        task = await self.session.get(Task, task_id)
        if not task:
            return None

        # exclude_unset=True 只取有傳入的欄位，沒傳的不更新
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(task, field, value)

        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def delete_task(self, task_id: uuid.UUID) -> None:
        await self.session.execute(delete(Task).where(Task.id == task_id))
        await self.session.commit()
