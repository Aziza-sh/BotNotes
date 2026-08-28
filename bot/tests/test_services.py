from unittest.mock import AsyncMock

import database.services as services


async def _make_note(**overrides):
    defaults = dict(
        user_id=1,
        building_name="Главный корпус",
        course=1,
        teacher="Иванов И.И.",
        note_name="Лекция 1",
        note_path="notes/f1.pdf",
        telegram_file_id="file-1",
        telegram_file_type="document",
    )
    defaults.update(overrides)
    return await services.create_note_service(**defaults)


# --- users -----------------------------------------------------------------


async def test_get_or_create_user_service_is_idempotent():
    first = await services.get_or_create_user_service(user_id=42)
    second = await services.get_or_create_user_service(user_id=42)

    assert first == {"user_id": 42}
    assert second == {"user_id": 42}
    assert len(await services.get_users_service()) == 1


async def test_is_admin_service_unknown_user_returns_message():
    result = await services.is_admin_service(user_id=999)
    assert result["message"]


async def test_change_admin_service_and_read_back():
    await services.get_or_create_user_service(user_id=7)

    changed = await services.change_admin_service(user_id=7, status=True)
    assert changed["message"] == ""

    status = await services.is_admin_service(user_id=7)
    assert status == {"status": True, "message": ""}


async def test_change_admin_service_unknown_user():
    result = await services.change_admin_service(user_id=12345, status=True)
    assert result["message"]


async def test_change_uploaded_notes_service_increments():
    await services.get_or_create_user_service(user_id=8)

    await services.change_uploaded_notes_service(user_id=8, amount=3)
    stat = await services.get_user_statistic_service(user_id=8)

    assert stat == {"uploaded_notes": 3, "message": ""}

    await services.change_uploaded_notes_service(user_id=8, amount=-1)
    stat = await services.get_user_statistic_service(user_id=8)
    assert stat["uploaded_notes"] == 2


# --- notes -------------------------------------------------------------------


async def test_create_note_service_creates_user_if_missing():
    result = await _make_note(user_id=55)

    assert result["message"] == ""
    assert result["telegram_user_id"] == 55
    assert result["data"].note_name == "Лекция 1"

    users = await services.get_users_service()
    assert {"user_id": 55} in users


async def test_get_notes_service_excludes_deleted(monkeypatch):
    monkeypatch.setattr(services, "delete_object", AsyncMock())

    kept = await _make_note(user_id=1, note_name="Оставить")
    await _make_note(user_id=1, note_name="Удалить")

    notes = await services.get_notes_service()
    assert len(notes) == 2

    await services.delete_note_service(kept["data"].id + 1)  # удаляем второй

    notes = await services.get_notes_service()
    assert len(notes) == 1
    assert notes[0]["note_name"] == "Оставить"


async def test_delete_note_service_calls_storage_delete(monkeypatch):
    mock_delete = AsyncMock()
    monkeypatch.setattr(services, "delete_object", mock_delete)

    note = await _make_note(note_path="notes/to-delete.pdf")
    result = await services.delete_note_service(note["data"].id)

    assert result == {"message": ""}
    mock_delete.assert_awaited_once_with("notes/to-delete.pdf")


async def test_delete_note_service_missing_note():
    result = await services.delete_note_service(999999)
    assert result["message"]


async def test_get_teachers_filters_by_course_and_building(monkeypatch):
    monkeypatch.setattr(services, "delete_object", AsyncMock())

    await _make_note(course=1, building_name="A", teacher="Иванов")
    await _make_note(course=1, building_name="A", teacher="Петров")
    await _make_note(course=2, building_name="A", teacher="Сидоров")
    await _make_note(course=1, building_name="B", teacher="Смирнов")

    teachers = await services.get_teachers(course=1, building_name="A")
    assert teachers == ["Иванов", "Петров"]

    teachers_all_buildings = await services.get_teachers(course=1)
    assert set(teachers_all_buildings) == {"Иванов", "Петров", "Смирнов"}


async def test_get_teacher_note_service_returns_matching_notes():
    await _make_note(course=1, building_name="A", teacher="Иванов", note_name="N1")
    await _make_note(course=1, building_name="A", teacher="Петров", note_name="N2")

    notes = await services.get_teacher_note_service(
        name="Иванов", course=1, building_name="A"
    )
    assert len(notes) == 1
    assert notes[0]["note_name"] == "N1"


async def test_custom_teacher_service_dedupes_active_entries():
    first = await services.add_custom_teacher_service(course=1, full_name="Кузнецов")
    second = await services.add_custom_teacher_service(course=1, full_name="Кузнецов")

    assert first["data"].id == second["data"].id

    teachers = await services.get_custom_teachers_service(course=1)
    assert teachers == ["Кузнецов"]


async def test_get_note_by_id_service_hides_deleted(monkeypatch):
    monkeypatch.setattr(services, "delete_object", AsyncMock())

    note = await _make_note()
    note_id = note["data"].id

    found = await services.get_note_by_id_service(note_id)
    assert found is not None
    assert found.id == note_id

    await services.delete_note_service(note_id)
    assert await services.get_note_by_id_service(note_id) is None


# --- search ------------------------------------------------------------------


async def test_search_notes_inline_matches_on_all_parts():
    await _make_note(
        building_name="Главный корпус",
        course=2,
        teacher="Иванов",
        note_name="Матан лекция",
    )
    await _make_note(
        building_name="Северный корпус",
        course=2,
        teacher="Петров",
        note_name="Физика семинар",
    )

    results = await services.search_notes_inline("Главный_2_Иванов_Матан")
    assert len(results) == 1
    assert results[0].note_name == "Матан лекция"


async def test_search_notes_inline_partial_query_building_only():
    await _make_note(building_name="Главный корпус", note_name="A")
    await _make_note(building_name="Северный корпус", note_name="B")

    results = await services.search_notes_inline("Главный")
    assert len(results) == 1
    assert results[0].note_name == "A"


async def test_search_notes_inline_empty_query_returns_all_non_deleted():
    await _make_note(note_name="A")
    await _make_note(note_name="B")

    results = await services.search_notes_inline("")
    assert len(results) == 2
