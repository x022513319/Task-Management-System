from fastapi import FastAPI

from app.api import auth

app = FastAPI()
app.include_router(auth.router)

# uvicorn 需要直接取得 app 物件，所以 app 要在 module 層級：

#   from fastapi import FastAPI
#   from app.api import auth

#   app = FastAPI()
#   app.include_router(auth.router)

#   然後用 uvicorn 啟動：
#   uvicorn app.main:app --reload
#   呼叫方式:
#   uvicorn {module_path}:{variable}

#   --reload 是開發模式，檔案變更時自動重啟。

# uvicorn app.main:app 啟動
#   │
#   ├─ 掃描所有 include_router 註冊的 endpoint
#   ├─ 讀取每個 endpoint 的型別註解、response_model、status_code
#   ├─ 自動產生 OpenAPI schema（JSON 格式）
#   └─ 自動建立兩個文件頁面

# http://localhost:8000/docs      → Swagger UI（互動式，可以直接測試 API）
# http://localhost:8000/redoc     → ReDoc（閱讀性較好）
# http://localhost:8000/openapi.json → 原始 OpenAPI schema
