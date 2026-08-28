from database.models import CustomTeacher, Notes, User


async def test_user_defaults():
    user = await User.create(user_id=111)

    assert user.uploaded_notes == 0
    assert user.messages_sent == 0
    assert user.is_admin is False
    assert user.is_deleted is False


async def test_version_bumped_on_save_via_pre_save_signal():
    # create() уже выполняет save() внутри, поэтому версия стартует с 1
    user = await User.create(user_id=222)
    assert user.version == 1

    user.messages_sent += 1
    await user.save()
    assert user.version == 2

    await user.save()
    assert user.version == 3


async def test_notes_fk_relation_to_user():
    user = await User.create(user_id=333)
    note = await Notes.create(
        user=user,
        building_name="Главный корпус",
        course=2,
        teacher="Иванов И.И.",
        note_name="Лекция 1",
        note_path="notes/abc.pdf",
        telegram_file_id="file123",
        telegram_file_type="document",
    )

    fetched = await Notes.get(id=note.id).select_related("user")
    assert fetched.user.user_id == 333
    assert fetched.is_deleted is False


async def test_custom_teacher_unique_per_row():
    t1 = await CustomTeacher.create(course=1, full_name="Петров П.П.")
    t2 = await CustomTeacher.create(course=1, full_name="Сидоров С.С.")

    assert t1.id != t2.id
    assert t1.course == t2.course == 1
