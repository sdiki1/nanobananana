from aiogram import types
from aiogram.dispatcher.filters import Text
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.common import send_main_menu
from db.repositories import get_user_by_tg_id, set_user_model
from keyboards.main import model_select_kb
from utils.constants import MODEL_NAMES


async def model_callback(query: types.CallbackQuery, session: AsyncSession) -> None:
    data = query.data.split(":", 1)[1]
    user = await get_user_by_tg_id(session, query.from_user.id)
    if not user:
        await query.answer("Сначала /start", show_alert=True)
        return

    if data == "back":
        await send_main_menu(query.message, user, edit=True)
        await query.answer()
        return

    if data not in MODEL_NAMES:
        await query.answer("Неизвестная модель", show_alert=True)
        return

    await set_user_model(session, user.id, data)
    await query.message.edit_reply_markup(reply_markup=model_select_kb(data))
    await query.answer(f"Выбрана модель {MODEL_NAMES[data]}")
    await send_main_menu(query.message, user, edit=True)


def register(dp):
    dp.register_callback_query_handler(model_callback, Text(startswith="model:"))
