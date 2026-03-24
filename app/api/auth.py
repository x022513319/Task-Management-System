# auth.py 認證相關（register, login, logout, refresh token）

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.redis import get_redis
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
    res: Response,
    req: UserCreate,
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> TokenResponse:
    auth_services = AuthServices(session=session, redis=redis)
    access_token, refresh_token = await auth_services.register(
        username=req.username, password=req.password
    )
    res.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
    return TokenResponse(access_token=access_token)


@router.post("/login", status_code=200)
async def login(
    res: Response,
    req: UserLogin,
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> TokenResponse:
    auth_services = AuthServices(session=session, redis=redis)
    access_token, refresh_token = await auth_services.login(
        username=req.username, password=req.password
    )
    res.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
    return TokenResponse(access_token=access_token)


# Request:     包含所有請求的資訊 (headers, cookies, body) (還有例如ip, method, url等)
# Response:    用來修改回應的物件
# res 負責:    Cookie、Header、Status Code
# return 負責: Response Body (JSON)
# FastAPI 合併 → 完整的 HTTP Response
@router.post("/refresh", status_code=200)
async def refresh(
    res: Response,
    req: Request,
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> TokenResponse:
    auth_services = AuthServices(session=session, redis=redis)
    refresh_token = req.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    # 不需要另外傳 user_id，
    # 因為 user_id 已經在 refresh token 的 JWT payload 裡了（sub 欄位）
    access_token, refresh_token = await auth_services.refresh(
        refresh_token=refresh_token
    )
    res.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
    return TokenResponse(access_token=access_token)


@router.post("/logout", status_code=200)
async def logout(
    res: Response,
    req: Request,
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> None:
    # 可以將 session, redis 拆成兩個service (AuthService, TokenService)
    # 不過對 practice project 來說有點 overdesigned 所以省略
    auth_services = AuthServices(session=session, redis=redis)
    refresh_token = req.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    await auth_services.logout(refresh_token=refresh_token)
    res.delete_cookie("refresh_token")
