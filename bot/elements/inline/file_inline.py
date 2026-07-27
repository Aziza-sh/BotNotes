import hashlib

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from elements.teachers import first_course, second_course, third_course, fourth_course
from database.services import get_teachers, get_custom_teachers_service


def teacher_token(full_name: str) -> str:
    """Стабильный короткий токен для полного ФИО.
    Кладём его в callback_data вместо самого имени, чтобы:
      - не обрезать ФИО под лимит текста кнопки/callback_data;
      - не терять отчество/длинные фамилии при сохранении в БД.
    """
    return hashlib.md5(full_name.encode("utf-8")).hexdigest()[:12]


async def get_upload_teachers_list(course: str | int) -> list[str]:
    """Собирает полный (не обрезанный) список преподавателей для курса:
    статический список + добавленные модератором кастомные преподаватели.
    Используется и при построении кнопок, и при разборе выбора преподавателя,
    чтобы токен всегда резолвился в одно и то же полное имя.
    """
    match int(course):
        case 1:
            TEACHERS = list(first_course)
        case 2:
            TEACHERS = list(second_course)
        case 3:
            TEACHERS = list(third_course)
        case 4:
            TEACHERS = list(fourth_course)
        case _:
            TEACHERS = list(first_course)

    custom_teachers = await get_custom_teachers_service(course=int(course))
    for full_name in custom_teachers:
        if full_name not in TEACHERS:
            TEACHERS.append(full_name)
    TEACHERS.sort()

    return TEACHERS


def buildings_buttons() -> InlineKeyboardMarkup:

    inline_kb_list = [
        [
            InlineKeyboardButton(text="Финуниверситет", callback_data="build fin"),
            InlineKeyboardButton(text="ЛФУ", callback_data="build lfu"),
        ],
        [
            InlineKeyboardButton(text="test | mfk", callback_data="build mfk"),
            InlineKeyboardButton(text="test | kip", callback_data="build kip"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def courses_buttons() -> InlineKeyboardMarkup:

    inline_kb_list = [
        [
            InlineKeyboardButton(text="1 курс", callback_data="course 1"),
            InlineKeyboardButton(text="2 курс", callback_data="course 2"),
        ],
        [
            InlineKeyboardButton(text="3 курс", callback_data="course 3"),
            InlineKeyboardButton(text="4 курс", callback_data="course 4"),
        ],
    ]

    inline_kb_list.append(
        [
            InlineKeyboardButton(
                text="Выбор учебного заведения ↩", callback_data="back_to_building"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


async def teachers_buttons(
    course: str | int, page: int = 0, in_page: int = 7
) -> InlineKeyboardMarkup:

    TEACHERS = await get_upload_teachers_list(course)

    start = page * in_page
    end = start + in_page
    inline_kb_list = []

    for full_name in TEACHERS[start:end]:
        # Раньше в callback_data клали ОБРЕЗАННОЕ имя (short_name), и именно
        # оно потом сохранялось в БД как ФИО преподавателя. Теперь в тексте
        # кнопки — полное имя (видно пользователю), а в callback_data —
        # только токен для однозначного поиска полного имени в хендлере.
        callback_data = f"t {teacher_token(full_name)}"
        inline_kb_list.append(
            [InlineKeyboardButton(text=full_name, callback_data=callback_data)]
        )

    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="← Назад", callback_data=f"page {course} {page - 1}"
            )
        )
    navigation_buttons.append(
        InlineKeyboardButton(text="Выбор курса ↩", callback_data="back_to_course")
    )
    if end < len(TEACHERS):
        navigation_buttons.append(
            InlineKeyboardButton(
                text="Вперёд →", callback_data=f"page {course} {page + 1}"
            )
        )

    inline_kb_list.append(navigation_buttons)

    inline_kb_list.append(
        [
            InlineKeyboardButton(
                text="🙋 Нет преподавателя в списке",
                callback_data=f"no_teacher {course}",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def buildings_buttons_view() -> InlineKeyboardMarkup:

    inline_kb_list = [
        [
            InlineKeyboardButton(text="Финуниверситет", callback_data="build_fin"),
            InlineKeyboardButton(text="ЛФУ", callback_data="build_lfu"),
        ],
        [
            InlineKeyboardButton(text="test | mfk", callback_data="build_mfk"),
            InlineKeyboardButton(text="test | kip", callback_data="build_kip"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def courses_buttons_view(building: str) -> InlineKeyboardMarkup:

    inline_kb_list = [
        [
            InlineKeyboardButton(text="1 курс", callback_data="course_1"),
            InlineKeyboardButton(text="2 курс", callback_data="course_2"),
        ],
        [
            InlineKeyboardButton(text="3 курс", callback_data="course_3"),
            InlineKeyboardButton(text="4 курс", callback_data="course_4"),
        ],
    ]
    inline_kb_list.append(
        [
            InlineKeyboardButton(
                text="Выбор места обучения ↩", callback_data="back_to_buildings_view"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


async def teachers_buttons_view(
    course: int,
    building: str,
    page: int = 0,
    in_page: int = 7,
) -> InlineKeyboardMarkup:

    TEACHERS = await get_teachers(course=course, building_name=building)
    inline_kb_list = []

    if not TEACHERS:
        inline_kb_list.append(
            [
                InlineKeyboardButton(
                    text=f"Конспектов {course} курса нет 💔", callback_data="noop"
                )
            ]
        )
        inline_kb_list.append(
            [
                InlineKeyboardButton(
                    text="Выбор курса ↩", callback_data="back_to_course_view"
                )
            ]
        )
        return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)

    start = page * in_page
    end = start + in_page

    for full_name in TEACHERS[start:end]:
        # Аналогично: полное имя — в тексте кнопки, токен — в callback_data.
        callback_data = f"t_{teacher_token(full_name)}"
        inline_kb_list.append(
            [InlineKeyboardButton(text=full_name, callback_data=callback_data)]
        )

    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="← Назад", callback_data=f"page_{course}_{page - 1}"
            )
        )
    navigation_buttons.append(
        InlineKeyboardButton(text="Выбор курса ↩", callback_data="back_to_course_view")
    )
    if end < len(TEACHERS):
        navigation_buttons.append(
            InlineKeyboardButton(
                text="Вперёд →", callback_data=f"page_{course}_{page + 1}"
            )
        )

    inline_kb_list.append(navigation_buttons)
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)
