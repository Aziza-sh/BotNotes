from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from api.app import app


@pytest.fixture
async def client():
    """
    Асинхронный клиент поверх ASGI-приложения без реального сервера.

    Важно: используем httpx.AsyncClient(transport=ASGITransport(...)) вместо
    fastapi.testclient.TestClient. TestClient гоняет приложение в отдельном
    потоке через свой event loop, из-за чего Tortoise теряет соединение с
    in-memory SQLite (оно живёт только в loop'е, где было создано) — тесты
    падают с "no such table". AsyncClient же выполняет запросы в том же
    event loop, что и тестовая функция и фикстура БД.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_root_health_check(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "BotNotes API"}


async def test_create_and_list_notes(client):
    payload = {
        "user_id": 100,
        "building_name": "Главный корпус",
        "course": 1,
        "teacher": "Иванов И.И.",
        "note_name": "Лекция по матанализу",
        "note_path": "notes/f.pdf",
        "telegram_file_id": "fid-1",
        "telegram_file_type": "document",
    }

    create_resp = await client.post("/api/v1/notes/", json=payload)
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["note_name"] == "Лекция по матанализу"
    assert body["is_deleted"] is False

    list_resp = await client.get("/api/v1/notes/")
    assert list_resp.status_code == 200
    assert any(n["id"] == body["id"] for n in list_resp.json())


async def test_delete_note_not_found_returns_404(client):
    response = await client.delete("/api/v1/notes/999999")
    assert response.status_code == 404


async def test_delete_note_success(client, monkeypatch):
    import database.services as services

    monkeypatch.setattr(services, "delete_object", AsyncMock())

    payload = {
        "user_id": 101,
        "building_name": "A",
        "course": 1,
        "teacher": "T",
        "note_name": "N",
        "note_path": "notes/del.pdf",
        "telegram_file_id": "fid-2",
        "telegram_file_type": "document",
    }
    create_resp = await client.post("/api/v1/notes/", json=payload)
    note_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/notes/{note_id}")
    assert response.status_code == 200

    listed = await client.get("/api/v1/notes/")
    listed_ids = [n["id"] for n in listed.json()]
    assert note_id not in listed_ids


async def test_users_get_or_create_and_admin_flow(client):
    create_resp = await client.post("/api/v1/users/555")
    assert create_resp.status_code == 201
    assert create_resp.json() == {"user_id": 555}

    admin_resp = await client.get("/api/v1/users/555/admin")
    assert admin_resp.status_code == 200
    assert admin_resp.json() == {"status": False}

    patch_resp = await client.patch("/api/v1/users/555/admin", json={"status": True})
    assert patch_resp.status_code == 200

    admin_resp = await client.get("/api/v1/users/555/admin")
    assert admin_resp.json() == {"status": True}


async def test_users_admin_status_unknown_user_404(client):
    response = await client.get("/api/v1/users/424242/admin")
    assert response.status_code == 404


async def test_notes_search_endpoint(client):
    await client.post(
        "/api/v1/notes/",
        json={
            "user_id": 200,
            "building_name": "Северный",
            "course": 3,
            "teacher": "Смирнов",
            "note_name": "Химия",
            "note_path": "notes/chem.pdf",
            "telegram_file_id": "fid-3",
            "telegram_file_type": "document",
        },
    )

    response = await client.get(
        "/api/v1/notes/search", params={"q": "Северный_3_Смирнов"}
    )
    assert response.status_code == 200
    results = response.json()
    assert any(n["note_name"] == "Химия" for n in results)


async def test_ai_summary_for_unknown_note_404(client):
    response = await client.get("/api/v1/ai/summary/999999")
    assert response.status_code == 404


async def test_ai_summary_contains_note_metadata(client):
    created_resp = await client.post(
        "/api/v1/notes/",
        json={
            "user_id": 300,
            "building_name": "Главный",
            "course": 2,
            "teacher": "Кузнецов",
            "note_name": "Физика",
            "note_path": "notes/phys.pdf",
            "telegram_file_id": "fid-4",
            "telegram_file_type": "document",
        },
    )
    created = created_resp.json()

    response = await client.get(f"/api/v1/ai/summary/{created['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["note_id"] == created["id"]
    assert "Физика" in body["summary"]
    assert "Кузнецов" in body["summary"]
