# tasks.py task CRUD
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..db.redis import get_redis
from ..db.session import get_db
from ..middlewares.auth import get_current_user
from ..models.user import User
from ..repositories.task import TaskRepository
from ..schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


# Cache 適合的條件：
#   1. 讀多寫少 — 資料頻繁被讀，但不常變動
#   2. 查詢代價高 — 例如複雜 JOIN、大量資料
#   3. 可以接受短暫不一致 — 不需要每次都是最新資料
@router.get("/", status_code=200)
async def get_tasks(
    redis: Redis = Depends(get_redis),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TaskRead]:
    redis_key = f"tasks:user:{current_user.id}"
    cached = await redis.get(redis_key)
    if cached:
        # .loads(): 字串 -> dict
        return [TaskRead(**t) for t in json.loads(cached)]

    task_repository = TaskRepository(session=session)
    tasks = await task_repository.get_tasks_by_user_id(current_user.id)
    tasks_reads = [TaskRead.model_validate(task) for task in tasks]

    # Task 是 SQLAlchemy model，不能直接放進 Redis，需要先轉成可序列化的格式
    # .model_dump(): TaskRead -> dict
    # .dumps(): dict -> 字串（JSON 字串，存入 Redis）
    # TaskRead 裡有 id: uuid.UUID，model_dump() 預設回傳 UUID 物件，
    # json.dumps 無法序列化它
    # 需要： mode="json"
    await redis.set(
        redis_key,
        json.dumps([t.model_dump(mode="json") for t in tasks_reads]),
        ex=60 * settings.TASK_CACHE_EXPIRE_MINUTES,  # measured in second
    )
    return tasks_reads


@router.post("/", status_code=201)
async def create_task(
    req: TaskCreate,
    redis: Redis = Depends(get_redis),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskRead:
    task_repository = TaskRepository(session=session)
    task = await task_repository.create_task(
        user_id=current_user.id, title=req.title, description=req.description
    )

    # Cache invalidation
    # 讓 cache 失效，否則 GET /tasks 會一直回傳舊資料
    redis_key = f"tasks:user:{current_user.id}"
    await redis.delete(redis_key)
    return TaskRead.model_validate(task)


@router.patch("/{task_id}", status_code=200)
async def update_task(
    task_id: uuid.UUID,
    req: TaskUpdate,
    redis: Redis = Depends(get_redis),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # 宣告了就會驗證，不一定要用到
) -> TaskRead:
    task_repository = TaskRepository(session=session)
    task = await task_repository.update_task(
        user_id=current_user.id, task_id=task_id, data=req
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Cache invalidation
    # 讓 cache 失效，否則 GET /tasks 會一直回傳舊資料
    redis_key = f"tasks:user:{current_user.id}"
    await redis.delete(redis_key)
    return TaskRead.model_validate(task)


@router.delete("/{task_id}", status_code=200)
async def delete_task(
    task_id: uuid.UUID,
    redis: Redis = Depends(get_redis),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    task_repository = TaskRepository(session=session)
    task = await task_repository.get_task_by_id(
        task_id=task_id, user_id=current_user.id
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Cache invalidation
    # 讓 cache 失效，否則 GET /tasks 會一直回傳舊資料
    redis_key = f"tasks:user:{current_user.id}"
    await redis.delete(redis_key)
    await task_repository.delete_task(user_id=current_user.id, task_id=task_id)
