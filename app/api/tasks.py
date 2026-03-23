# tasks.py task CRUD
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_db
from ..middlewares.auth import get_current_user
from ..models.user import User
from ..repositories.task import TaskRepository
from ..schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", status_code=200)
async def get_tasks(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TaskRead]:
    task_repository = TaskRepository(session=session)
    tasks = await task_repository.get_tasks_by_user_id(current_user.id)
    return [TaskRead.model_validate(task) for task in tasks]


@router.post("/", status_code=201)
async def create_task(
    req: TaskCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskRead:
    task_repository = TaskRepository(session=session)
    task = await task_repository.create_task(
        user_id=current_user.id, title=req.title, description=req.description
    )
    return TaskRead.model_validate(task)


@router.patch("/{task_id}", status_code=200)
async def update_task(
    task_id: uuid.UUID,
    req: TaskUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # 宣告了就會驗證，不一定要用到
) -> TaskRead:
    task_repository = TaskRepository(session=session)
    task = await task_repository.update_task(
        user_id=current_user.id, task_id=task_id, data=req
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskRead.model_validate(task)


@router.delete("/{task_id}", status_code=200)
async def delete_task(
    task_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    task_repository = TaskRepository(session=session)
    task = await task_repository.get_task_by_id(
        task_id=task_id, user_id=current_user.id
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await task_repository.delete_task(user_id=current_user.id, task_id=task_id)
