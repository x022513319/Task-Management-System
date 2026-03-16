# 專案：個人任務管理 API

## 專案描述
多用戶任務管理系統，用戶可以註冊登入後管理自己的任務（CRUD）。
主要學習目的是實作 JWT 認證授權與 Redis 快取。

## 功能需求
- 用戶註冊 / 登入 / 登出
- JWT access token + refresh token 機制
- 任務的新增、查詢、更新、刪除（每個用戶只能操作自己的任務）
- Redis 快取任務列表查詢結果
- Redis 實作 API Rate Limiting
- Docker 化 + GitHub Actions CI/CD + 部署到 Azure Container Apps

## 技術棧
- FastAPI, PostgreSQL, Redis, Docker
- SQLAlchemy + Alembic（ORM + migration）
- python-jose（JWT）、bcrypt（密碼 hash）
- pytest + httpx（測試）

## 學習目標（優先順序）
1. JWT / Refresh Token 機制
2. Redis Cache-aside 模式與 Cache invalidation
3. GitHub Actions CI/CD

## 暫時不需要實作
- RFC 9457 錯誤標準化
- 完整 logging / monitoring
- OAuth 第三方登入

## 對 Claude 的要求
- 這是學習專案，解釋為什麼這樣做，不只是給程式碼
- 遇到我不熟的概念請主動說明
- 不要一次幫我做太多，讓我自己動手