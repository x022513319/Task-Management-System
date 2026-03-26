# multi-stage building

# step 1. builder
# base image
FROM python:3.13-slim AS builder

# COPY --from=<來源image>  <來源路徑>  <目標路徑>
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Optimization
ENV UV_COMPILE_BYTECODE=1 \
# Caching
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# 先只複製依賴定義檔（利用 cache 加速）
# 如果一開始就 COPY . . 這行下面的全部都要重跑，
# 每次跑uv sync就會很慢
# 參照：Docker 的 layer cache 機制
COPY pyproject.toml uv.lock ./

# --frozen 完全按照 uv.lock 安裝，不允許任何版本變動，確保 CI / Docker 環境可重現
# --no-dev 不安裝 dev 依賴（例如 ruff、mypy、pytest)
RUN uv sync --frozen --no-dev

# copy 整個 project
COPY . .

# ------------------------------------------
# step 2. runtime
# 只保留執行所需的東西，不含 uv、build 工具等
FROM python:3.13-slim

WORKDIR /app

# 只從 builder 複製裝好的虛擬環境和程式碼
COPY --from=builder /app /app/

# PATH 用 : 分隔多個目錄
# 讓系統直接使用 .venv 裡的 Python
# 輸入 python 時系統會依序找python執行檔
ENV PATH="/app/.venv/bin:$PATH"
#         ↑               ↑
#   新增這個目錄到最前面   保留原本的 PATH

# 預設 127.0.0.1 在 container 裡外面連不進來
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]