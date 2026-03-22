# auth.py 認證相關（register, login, logout, refresh token）

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_db
from ..schemas.user import TokenResponse, UserCreate, UserLogin
from ..services.auth import AuthServices

# prefix: 自動幫這個 router 下的所有 endpoint 加上路徑前綴
# tags: Swagger UI 的分組標籤**，把相關的 endpoint 歸類在一起，純粹是文件用途
# 不影響實際行為
#
# e.g.
# users
#  ├── GET    /users/
#  ├── GET    /users/{user_id}
#  ├── POST   /users/
#  └── PATCH  /users/{user_id}
#
# auth
#  ├── POST   /auth/login
#  └── POST   /auth/refresh

router = APIRouter(prefix="/auth", tags=["auth"])


# FastAPI 收到 request 時會：
#    1. 呼叫 get_db() 取得 session
#    2. 把 session 注入到 db 參數
#    3. 執行 register()
#    4. 結束後自動關閉 session（因為 get_db 用 yield）


@router.post("/register", status_code=201)
# 不加括號 - 把 get_db 函式本身傳給 Depends
async def register(
    req: UserCreate, session: AsyncSession = Depends(get_db)
) -> TokenResponse:
    auth_services = AuthServices(session=session)
    return await auth_services.register(username=req.username, password=req.password)


@router.post("/login", status_code=200)
async def login(
    req: UserLogin, session: AsyncSession = Depends(get_db)
) -> TokenResponse:
    auth_services = AuthServices(session=session)
    return await auth_services.login(username=req.username, password=req.password)
