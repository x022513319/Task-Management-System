import pytest
from httpx import AsyncClient

# 若以function為單位，則 asyncio_mode = "auto" 時
# 不需要加 @pytest.mark.asyncio

# 也可以加在pyproject:
# [tool.pytest.ini_options]
# asyncio_mode = "auto"


@pytest.mark.asyncio
class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        # Arrange & Act
        response = await client.post(
            "/auth/register", json={"username": "test_user", "password": "test_user"}
        )

        # Assert
        assert response.status_code == 201

        data = response.json()
        assert "access_token" in data
        assert data["access_token"] is not None

        assert "refresh_token" in response.cookies

    async def test_register_duplicate(self, client: AsyncClient):
        # Arrange
        response_first = await client.post(
            "auth/register",
            json={"username": "test_user", "password": "test_user_first"},
        )

        # Act
        response_second = await client.post(
            "auth/register",
            json={"username": "test_user", "password": "test_user_second"},
        )

        assert response_first.status_code == 201
        assert response_second.status_code == 409


@pytest.mark.asyncio
class TestLogin:
    async def test_login_success(self, client: AsyncClient, registered_user: dict):
        # Act
        refresh_res = await client.post(
            "auth/login",
            json={
                "username": registered_user["username"],
                "password": registered_user["password"],
            },
        )

        # Assert
        assert refresh_res.status_code == 200
        data = refresh_res.json()
        assert "access_token" in data
        assert data["access_token"] is not None

        assert "refresh_token" in refresh_res.cookies

    async def test_login_wrong_password(
        self, client: AsyncClient, registered_user: dict
    ):
        # Act
        refresh_res = await client.post(
            "auth/login",
            json={
                "username": registered_user["username"],
                "password": "wrong_password",
            },
        )

        # Assert
        assert refresh_res.status_code == 401

    async def test_login_nonexistent_user(
        self, client: AsyncClient, registered_user: dict
    ):
        # Act
        refresh_res = await client.post(
            "auth/login",
            json={
                "username": "nonexistent_user",
                "password": registered_user["password"],
            },
        )

        # Assert
        assert refresh_res.status_code == 401


@pytest.mark.asyncio
class TestRefresh:
    async def test_refresh_success(self, client: AsyncClient, registered_user: dict):
        # Arrange
        old_refresh_token = registered_user["refresh_token"]
        client.cookies.set("refresh_token", registered_user["refresh_token"])

        # Act
        res = await client.post("/auth/refresh")

        # Assert
        assert res.status_code == 200
        data = res.json()

        assert "access_token" in data
        assert data["access_token"] is not None

        new_fresh_token = res.cookies.get("refresh_token")
        assert new_fresh_token is not None
        assert new_fresh_token != old_refresh_token

    async def test_refresh_no_cookie(self, client: AsyncClient, registered_user: dict):
        # Arrange
        client.cookies.delete("refresh_token")

        # Act
        res = await client.post("/auth/refresh")

        # Assert
        assert res.status_code == 401


@pytest.mark.asyncio
class TestLogout:
    async def test_logout_success(self, client: AsyncClient, registered_user: dict):
        # Act
        res = await client.post("/auth/logout")

        # Assert
        assert res.status_code == 200

        refresh_res = await client.post("/auth/refresh")
        assert refresh_res.status_code == 401

    async def test_logout_no_cookie(self, client: AsyncClient, registered_user: dict):
        # Arrange
        client.cookies.delete("refresh_token")

        # Act
        res = await client.post("/auth/logout")

        # Assert
        assert res.status_code == 401
