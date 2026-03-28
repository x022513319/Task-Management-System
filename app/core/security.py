import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from jose import JWTError, jwt

from .config import settings


def create_access_token(user_id: uuid.UUID) -> str:
    """
    JWT payload:
        iss (Issuer): Who created the token
        sub (Subject): The user ID (e.g., user GUID)
        exp (Expiration Time): When the token expires
        aud (Audience): Who the token is intended for
        iat (Issued At): When the token was created
    """
    payload = {
        "iss": settings.JWT_ISS,
        "sub": str(user_id),
        "exp": datetime.now(UTC)
        + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": str(uuid.uuid4()),  # 避免同一秒內產生相同的JWT，加上jti讓每次JWT都不同
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: uuid.UUID) -> str:
    """
    JWT payload:
        iss (Issuer): Who created the token
        sub (Subject): The user ID (e.g., user GUID)
        exp (Expiration Time): When the token expires
        aud (Audience): Who the token is intended for
        iat (Issued At): When the token was created
    """
    payload = {
        "iss": settings.JWT_ISS,
        "sub": str(user_id),
        "exp": datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "jti": str(uuid.uuid4()),  # 避免同一秒內產生相同的JWT，加上jti讓每次JWT都不同
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        # python-jose 的 jwt.decode() 會預設檢查 exp
        payload = jwt.decode(token, settings.JWT_SECRET, [settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
