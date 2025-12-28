from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories import get_or_create_user
from handlers.common import send_main_menu


async def cmd_start(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    args = message.get_args()
    ref_code = None
    if args.startswith("ref_"):
        ref_code = args.replace("ref_", "", 1)

    user = await get_or_create_user(session, message.from_user.id, message.from_user.username, ref_code)
    await state.finish()

    await send_main_menu(message, user)
    await message.answer(
        "✋ Стой, стой! Сначала небольшая, но важная инструкция 👉 Изучи её.\n\n"
        "Если уже читал, то просто 📎 отправь фото в бота, как обычное сообщение."
    )


def register(dp):
    dp.register_message_handler(cmd_start, CommandStart())
