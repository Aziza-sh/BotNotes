from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.markdown import hlink
from aiogram.types import Message, ReplyKeyboardRemove

from database.services import get_or_create_user_service, get_users_service
from functions.greeting import send_greeting

from elements.inline.other_inline import support_button
from elements.keybord.kb import main_kb, cancel_kb

from events.states_group import Utils
from config.advertisement import support_link

router = Router()


# --- Основная панель --- #
@router.message(Command("start"))
async def start_cmd(message: Message, state: FSMContext):
    # Если стадия существует, выходим из неё
    if await state.get_state() is not None:
        await message.answer(text="🔎✨", reply_markup=ReplyKeyboardRemove())
        await state.clear()

    await get_or_create_user_service(user_id=message.from_user.id)

    await message.answer(
        text=f"{send_greeting(username=message.from_user.first_name)}\
            \nВыберите, что Вы хотите сделать:",
        reply_markup=main_kb(),
    )


# --- Информационнная панель --- #
@router.message(Command("info"))
async def info_cmd(message: Message, state: FSMContext):
    # Если стадия существует, выходим из неё
    if await state.get_state() is not None:
        await message.answer(text="🔎✨", reply_markup=ReplyKeyboardRemove())
        await state.clear()

    await get_or_create_user_service(user_id=message.from_user.id)

    botname = message.bot.config["SETTINGS"]["name"]
    message_text = (
        f"<b>Вы используете  {hlink(botname, support_link)} v{message.bot.config['SETTINGS']['version']}:</b>"
        f"\n\n 1. Данный бот предназначен для просмотра и выкладывания конспектов, чтобы все теория, предоставляемая преподавателями была достпуна в любое время. \n\n"
        f" 2. Чтобы просмотреть конспект, нужно после команды /start нажать на кнопку 'Просмотреть конспект 👀' и дальше нажимать на кнопки, выбирая нужный курс и преподавателя. \n <b>Примечание!</b> Данный проект ещё в разработке и не на каждого преподавателя есть конспекты. Если что, когда конспектов на определённого преподавателя нет, то преподаватель не высвечивается пользователю. \n\n"
        f" 3. Чтобы выложить конспект, после команды /start надо будет нажать на кнопку 'Поделиться конспектом ✉️' и заполнить анкету, которая собирает информацию об конспекте, и сам конспект. Сначала он отправляется на модерацию и, если он её проходит, публикуется. \n <b> Примечание!</b> О Любом изменении статуса отправленного конспекта бот будет уведомлять. \n\n "
        f" 4. Чтобы связаться с поддержкой бота, присоединитесь к <b>{hlink('группе', support_link)}</b> и задайте вопрос в нужном топике."
    )

    await message.answer(text=message_text, reply_markup=support_button().as_markup())


# --- Отправка статистики --- #
@router.message(Command("statistic", "bin"))
async def statistic_cmd(message: Message, state: FSMContext):
    # Если стадия существует, выходим из неё
    if await state.get_state() is not None:
        await message.answer(text="🔎✨", reply_markup=ReplyKeyboardRemove())
        await state.clear()

    if int(message.chat.id) in map(int, message.bot.ADMIN_CHATS):
        users_data = await get_users_service()
        if users_data:
            users_count = f"<b>Пользователей:</b> <code>{len(users_data)}</code>"
        else:
            users_count = "<b>Информации о пользователях нет</b>!"

        await message.answer(
            text=f"<b>СТАТИСТИКА:</b>\
                \n\n{users_count}"
        )


# --- Перейти в рассылку -> Написать текст --- #
@router.message(Command("mailing", "bin2"))
async def mailing_cmd(message: Message, state: FSMContext):
    # Если стадия существует, выходим из неё
    if await state.get_state() is not None:
        await message.answer(text="🔎✨", reply_markup=ReplyKeyboardRemove())
        await state.clear()

    if int(message.chat.id) in map(int, message.bot.ADMIN_CHATS):
        await message.answer(
            text="💥 Введите <u>текст</u> или прикрепите <u>медиаконтент</u>, который будет отправлен всем пользователям:",
            reply_markup=cancel_kb(),
        )
        await state.set_state(Utils.mailing)
