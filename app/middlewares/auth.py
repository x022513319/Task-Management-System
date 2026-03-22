import uuid

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import verify_token
from ..db.session import get_db
from ..models.user import User
from ..repositories.user import UserRepository

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials  # 取出 Bearer 後面的 token
    user_repository = UserRepository(session=session)
    result = verify_token(token=token)
    # payload of JWT: ["sub", "exp", "iss"]
    user_id = uuid.UUID(result["sub"])
    user = await user_repository.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid Credentials")

    return user


# from fastapi.security import OAuth2PasswordBearer
# # tokenUrl 是告訴 Swagger UI 登入的 endpoint 在哪，不影響實際驗證
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# # 自動從 Authorization header 取出 token
# async def get_current_user(
#     token: str = Depends(oauth2_scheme),
#     session: AsyncSession = Depends(get_db)
# ) -> User:
#     user_repository = UserRepository(session=session)
#     result = verify_token(token=token)
#     # payload of JWT: ["sub", "exp", "iss"]
#     user_id = uuid.UUID(result["sub"])
#     user = await user_repository.get_user_by_id(user_id=user_id)
#     if not user:
#         raise HTTPException(status_code=401, detail="Invalid Credentials")

#     return user

# -----------------------------------------------------
# 若不使用 FastAPI 內建的 OAuth2PasswordBearer
# 也可以手搓

# from fastapi import Request

# async def get_current_user(req: Request) -> User:
#     auth_header = req.headers.get("Authorization")
#     if not auth_header or not auth_header.startswith("Bearer "):
#         raise HTTPException(status_code=401)

#     token = auth_header.split(" ")[1] # Bear <token> 的 token 部分
#     ...
