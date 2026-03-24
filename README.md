# Task Management System

多用戶任務管理 API，用戶可以註冊登入後管理自己的任務（CRUD）。

學習目標：JWT 認證授權機制、Redis Cache-aside 模式、GitHub Actions CI/CD。

## 技術棧

- **Web Framework**: FastAPI
- **Database**: PostgreSQL 17 + SQLAlchemy (async) + Alembic
- **Cache**: Redis 8.4
- **認證**: python-jose (JWT) + bcrypt
- **測試**: pytest + httpx
- **容器化**: Docker + Docker Compose

## 專案結構

```
app/
├── api/
│   ├── auth.py        # 認證端點（register, login, logout, refresh）
│   └── tasks.py       # 任務 CRUD 端點
├── core/
│   ├── config.py      # 環境變數設定（pydantic-settings）
│   └── security.py    # JWT 簽發 / 驗證
├── db/
│   ├── session.py     # PostgreSQL async session
│   ├── redis.py       # Redis connection pool
│   └── base.py        # SQLAlchemy Base
├── middlewares/
│   └── auth.py        # JWT 驗證 middleware（get_current_user）
├── models/
│   ├── user.py        # User ORM model
│   └── task.py        # Task ORM model
├── repositories/
│   ├── user.py        # User DB 操作
│   └── task.py        # Task DB 操作
├── schemas/
│   ├── user.py        # User Pydantic schemas
│   └── task.py        # Task Pydantic schemas
├── services/
│   └── auth.py        # 認證商業邏輯（AuthServices）
└── main.py            # FastAPI app 入口
```

## API 端點

### 認證（`/auth`）

| Method | Path              | 說明               | 需要認證 |
|--------|-------------------|--------------------|----------|
| POST   | `/auth/register`  | 用戶註冊           | 否       |
| POST   | `/auth/login`     | 用戶登入           | 否       |
| POST   | `/auth/refresh`   | 刷新 access token  | Cookie   |
| POST   | `/auth/logout`    | 登出               | Cookie   |

### 任務（`/tasks`）

| Method | Path               | 說明         | 需要認證 |
|--------|--------------------|--------------|----------|
| GET    | `/tasks/`          | 取得任務列表 | JWT      |
| POST   | `/tasks/`          | 新增任務     | JWT      |
| PATCH  | `/tasks/{task_id}` | 更新任務     | JWT      |
| DELETE | `/tasks/{task_id}` | 刪除任務     | JWT      |

### 認證流程

1. 登入後取得 `access_token`（JSON body）與 `refresh_token`（HttpOnly Cookie）
2. 每個需要認證的 API 在 `Authorization: Bearer <access_token>` header 帶入 access token
3. Access token 過期後，呼叫 `/auth/refresh` 自動換發新的 token pair
4. Refresh token 儲存於 Redis，登出時從 Redis 撤銷（revocation）

## 快速開始

### 1. 環境變數

建立 `.env` 檔案：

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=task_db
POSTGRES_PORT=5432

SQLALCHEMY_DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/task_db
REDIS_DATABASE_URL=redis://localhost:6379/0
REDIS_PORT=6379

JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 2. 啟動資料庫與 Redis

```bash
docker compose up -d
```

### 3. 安裝依賴

```bash
pip install -r requirements.txt
```

### 4. 執行 Migration

```bash
alembic upgrade head
```

### 5. 啟動 API Server

```bash
uvicorn app.main:app --reload
```

API 文件：http://localhost:8000/docs

## 開發重點筆記

### JWT 雙 Token 機制

- **Access Token**：短效（預設 30 分鐘），放在 Authorization header，用於 API 授權
- **Refresh Token**：長效（預設 7 天），放在 HttpOnly Cookie，用於換發新的 access token
- Refresh token 同時存入 Redis，登出時從 Redis 刪除，實現真正的 token 撤銷（revocation）

### Redis Cache-aside 模式（待實作）

讀取時先查 Redis，cache miss 才查 DB，寫入 DB 後同步 invalidate cache。

## 學習進度

- [x] JWT access token + refresh token 機制
- [x] Redis 儲存 refresh token（revocation）
- [ ] Redis Cache-aside（任務列表快取）
- [ ] Redis API Rate Limiting
- [ ] Docker 化（應用程式）
- [ ] GitHub Actions CI/CD
- [ ] 部署到 Azure Container Apps
