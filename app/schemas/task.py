import uuid

from pydantic import BaseModel, ConfigDict


class TaskBase(BaseModel):
    # user_id 不需要，user由JWT token取得
    title: str
    description: str | None = None


class TaskCreate(TaskBase):
    pass


class TaskRead(TaskBase):
    id: uuid.UUID
    is_completed: bool

    model_config = ConfigDict(from_attributes=True)


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    is_completed: bool | None = None
