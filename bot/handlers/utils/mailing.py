import asyncio
import time

from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from events.states_group import Utils

from database.services import get_users_service

router = Router()


# --- Обработчик сообщения и рассылка всем пользователям ---
@router.message(Utils.mailing)
async def mailing_send(message: Message, state: FSMContext):
    msg = await message.answer(
        text="<b>💥💥 Процесс отправки будет запущен через <i>10 секунд</i>.</b>\nВы можете <b>отменить</b> это действие, вернувшись в /start!"
    )
    await asyncio.sleep(10)  # Глушим на 10 секунд перед началом рассылки

    # Если пользователь отменил, то останавливаем рассылку
    if await state.get_state() != Utils.mailing:
        return

    # Получаем список всех анкет
    all_profiles = await get_users_service()
    user_counter = 0

    await msg.delete()
    await message.answer(text=f"<b>💥💥💥 Рассылка запущена!</b>")
    start_time = time.time()  # Запоминаем время начала рассылки

    # Рассылка по пользователям и чатам
    for user_id in all_profiles:
        chat_id = user_id["user_id"] if "user_id" in user_id else user_id["chat_id"]
        status = True

        try:
            await message.bot.copy_message(
                chat_id=chat_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
            )
        except:
            status = False

        if status is True:
            user_counter += 1

    elapsed_time = time.time() - start_time  # Вычисляем время, затраченное на рассылку

    await message.answer(
        text=f"<b>Рассылка закончена!</b>\n\
            \nОтправлено пользователям: {user_counter}/{len(all_profiles)}.\
            \n\n<i>Рассылка длилась <b>{elapsed_time:.2f} сек.</b></i>"
    )
    await state.clear()
