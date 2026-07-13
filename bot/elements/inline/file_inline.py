from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from elements.teachers import first_course, second_course, third_course, fourth_course
from database.services import get_teachers


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


def teachers_buttons(
    course: str | int, page: int = 0, in_page: int = 7
) -> InlineKeyboardMarkup:

    match int(course):
        case 1:
            TEACHERS = first_course
        case 2:
            TEACHERS = second_course
        case 3:
            TEACHERS = third_course
        case 4:
            TEACHERS = fourth_course
        case _:
            TEACHERS = first_course

    start = page * in_page
    end = start + in_page
    inline_kb_list = []

    for full_name in TEACHERS[start:end]:
        name_parts = full_name.split()
        if not name_parts[0].isalpha():
            short_name = name_parts[0][:20]
        elif len(name_parts) > 1:
            short_name = f"{name_parts[0][:15]} {name_parts[1][:14]}"
        else:
            short_name = name_parts[0][:20]

        callback_data = f"t {short_name}"
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
        name_parts = full_name.split()
        if not name_parts[0].isalpha():
            short_name = name_parts[0][:20]
        elif len(name_parts) > 1:
            short_name = f"{name_parts[0][:15]}_{name_parts[1][:14]}"
        else:
            short_name = name_parts[0][:20]

        callback_data = f"t_{short_name}"
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
