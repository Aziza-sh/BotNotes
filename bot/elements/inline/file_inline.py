from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from elements.teachers import (
    first_course,
    second_course,
    third_course,
    fourth_course
)
from database.services import get_teachers


def courses_buttons():
    inline_kb_list = [
        [InlineKeyboardButton(text="1 курс", callback_data='course 1'), InlineKeyboardButton(text="2 курс", callback_data='course 2')],
        [InlineKeyboardButton(text="3 курс", callback_data='course 3'), InlineKeyboardButton(text="4 курс", callback_data='course 4')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


# Берутся только преподаватели необходимого нам курса
# Разделение в callback по пробелу
def teachers_buttons(course: str | int, page: int = 0, in_page: int = 7):
    match int(course):
        case 1: TEACHERS = first_course
        case 2: TEACHERS = second_course
        case 3: TEACHERS = third_course
        case 4: TEACHERS = fourth_course
        case _: TEACHERS = first_course

    start = page * in_page
    end = start + in_page
    inline_kb_list = []
    for full_name in TEACHERS[start:end]:
        name_parts = full_name.split()
        if not name_parts[0].isalpha(): # Если есть спец.символы (это уже делает фамилию с большей вероятностью уникальной), берём только фамилию
            short_name = name_parts[0][:20]
        else:
            if len(name_parts) > 1: # Если есть и фамилия и имя
                short_name = f"{name_parts[0][:15]} {name_parts[1][:14]}"
            else:  # Если есть только фамилия
                short_name = name_parts[0][:20]
        
        callback_data = f"t {short_name}"
        inline_kb_list.append([
            InlineKeyboardButton(
                text=full_name,
                callback_data=callback_data
            )
        ])

    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(
            InlineKeyboardButton(text="← Назад", callback_data=f'page {course} {page - 1}')
        )

    navigation_buttons.append(
        InlineKeyboardButton(text="Выбор курса ↩", callback_data='back_to_course')
    )
    if end < len(TEACHERS):
        navigation_buttons.append(
            InlineKeyboardButton(text="Вперёд →", callback_data=f'page {course} {page + 1}')
        )

    inline_kb_list.append(navigation_buttons)
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def courses_buttons_view():
    inline_kb_list = [
        [InlineKeyboardButton(text="1 курс", callback_data='course_1'), InlineKeyboardButton(text="2 курс", callback_data='course_2')],
        [InlineKeyboardButton(text="3 курс", callback_data='course_3'), InlineKeyboardButton(text="4 курс", callback_data='course_4')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


# Берутся только те преподаватели ИЗ БАЗЫ, чьи конспекты у нас есть
# Разделение в callback по "_"
async def teachers_buttons_view(course: int, page: int = 0, in_page: int = 7):
    TEACHERS = await get_teachers(course=course)
    inline_kb_list = []
    if not TEACHERS: # Нет преподавателей — одна информирующая кнопка + возврат
        inline_kb_list.append([
            InlineKeyboardButton(
                text=f"Конспектов {course} курса нет 💔",
                callback_data="noop"
            )
        ])
        inline_kb_list.append([
            InlineKeyboardButton(text="Выбор курса ↩", callback_data='back_to_course_view')
        ])
        return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)

    start = page * in_page
    end = start + in_page
    for full_name in TEACHERS[start:end]:
        name_parts = full_name.split()
        if not name_parts[0].isalpha(): # Если есть спец.символы (это уже делает фамилию с большей вероятностью уникальной), берём только фамилию
            short_name = name_parts[0][:20]
        else:
            if len(name_parts) > 1: # Если есть и фамилия и имя
                short_name = f"{name_parts[0][:15]}_{name_parts[1][:14]}"
            else:  # Если есть только фамилия
                short_name = name_parts[0][:20]
        
        callback_data = f"t_{short_name}"
        inline_kb_list.append([
            InlineKeyboardButton(
                text=full_name,
                callback_data=callback_data
            )
        ])

    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(
            InlineKeyboardButton(text="← Назад", callback_data=f"page_{course}_{page - 1}")
        )

    navigation_buttons.append(
        InlineKeyboardButton(text="Выбор курса ↩", callback_data='back_to_course_view')
    )
    if end < len(TEACHERS):
        navigation_buttons.append(
            InlineKeyboardButton(text="Вперёд →", callback_data=f"page_{course}_{page + 1}")
        )

    inline_kb_list.append(navigation_buttons)
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)
