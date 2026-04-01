import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestGetTasks:
    async def test_get_tasks_empty(self, client: AsyncClient, registered_user: dict):
        # Arrange
        headers = {"Authorization": f"Bearer {registered_user['access_token']}"}

        # Act
        res = await client.get("/tasks/", headers=headers)

        # Assert
        assert res.status_code == 200
        assert res.json() == []

    async def test_get_tasks_success(
        self, client: AsyncClient, registered_user: dict, created_task: dict
    ):
        # Arrange
        headers = {"Authorization": f"Bearer {registered_user['access_token']}"}

        # Act
        res = await client.get("/tasks/", headers=headers)

        # Assert
        assert res.status_code == 200
        data = res.json()

        assert len(data) == 1
        assert data[0]["id"] is not None
        assert data[0]["title"] == created_task["title"]
        assert data[0]["description"] == created_task["description"]

    async def test_get_tasks_unauthorized(
        self, client: AsyncClient, registered_user: dict
    ):
        # Act
        res = await client.get("/tasks/")

        # Assert
        assert res.status_code == 401


@pytest.mark.asyncio
class TestCreateTask:
    async def test_create_task_success(
        self, client: AsyncClient, registered_user: dict
    ):
        # Arrange
        headers = {"Authorization": f"Bearer {registered_user['access_token']}"}
        task = {"title": "test_title", "description": "test_description"}

        # Act
        res = await client.post("/tasks/", headers=headers, json=task)

        # Assert
        assert res.status_code == 201
        data = res.json()

        assert data["title"] == task["title"]
        assert data["description"] == task["description"]

    async def test_create_task_unauthorized(
        self, client: AsyncClient, registered_user: dict
    ):
        # Arrange
        task = {"title": "test_title", "description": "test_description"}

        # Act
        res = await client.post("/tasks/", json=task)

        # Assert
        assert res.status_code == 401


@pytest.mark.asyncio
class TestUpdateTask:
    async def test_update_task_success(
        self, client: AsyncClient, registered_user: dict, created_task: dict
    ):
        # Arrange
        headers = {"Authorization": f"Bearer {registered_user['access_token']}"}
        update_task = {"title": "test_updated", "description": "test_updated"}

        # Act
        res = await client.patch(
            f"/tasks/{created_task['id']}", headers=headers, json=update_task
        )

        # Assert
        assert res.status_code == 200
        data = res.json()

        assert data["id"] == created_task["id"]  # unchanged
        assert data["title"] == update_task["title"]
        assert data["description"] == update_task["description"]
        assert data["is_completed"] == created_task["is_completed"]  # unchanged

    async def test_update_task_not_found(
        self, client: AsyncClient, registered_user: dict
    ):
        # Arrange
        headers = {"Authorization": f"Bearer {registered_user['access_token']}"}
        update_task = {"title": "test_updated", "description": "test_updated"}
        fake_id = str(uuid.uuid4())

        # Act
        res = await client.patch(f"/tasks/{fake_id}", headers=headers, json=update_task)

        # Assert
        assert res.status_code == 404  # Task not found


@pytest.mark.asyncio
class TestDeleteTask:
    async def test_delete_task_success(
        self, client: AsyncClient, registered_user: dict, created_task: dict
    ):
        # Arrange
        headers = {"Authorization": f"Bearer {registered_user['access_token']}"}

        # Act
        res = await client.delete(f"/tasks/{created_task['id']}", headers=headers)
        assert res.status_code == 200

        # Assert
        get_res = await client.get("/tasks/", headers=headers)
        assert get_res.json() == []

    async def test_delete_task_not_found(
        self, client: AsyncClient, registered_user: dict
    ):
        # Arrange
        headers = {"Authorization": f"Bearer {registered_user['access_token']}"}
        fake_id = str(uuid.uuid4())

        # Act
        res = await client.delete(f"/tasks/{fake_id}", headers=headers)

        # Assert
        assert res.status_code == 404  # Task not found
