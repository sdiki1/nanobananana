from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.common import send_main_menu
from db.repositories import get_user_by_tg_id, set_user_preset
from keyboards.main import presets_kb
from utils.presets import get_preset
from utils.states import GenerationStates


async def preset_callback(query: types.CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = query.data.split(":", 1)[1]
    user = await get_user_by_tg_id(session, query.from_user.id)
    if not user:
        await query.answer("Сначала /start", show_alert=True)
        return

    if data == "back":
        await send_main_menu(query.message, user, edit=True)
        await query.answer()
        return

    if data == "reset":
        await set_user_preset(session, user.id, None)
        await state.finish()
        await query.answer("Пресет сброшен", show_alert=False)
        await query.message.edit_reply_markup(reply_markup=presets_kb(None))
        return

    preset = get_preset(data)
    if not preset:
        await query.answer("Пресет не найден", show_alert=True)
        return

    await set_user_preset(session, user.id, preset.key)
    await state.set_state(GenerationStates.waiting_photo_preset.state)
    await query.message.edit_reply_markup(reply_markup=presets_kb(preset.key))
    await query.answer("Пресет выбран")
    await query.message.answer_photo(
        preset.preview_url,
        caption=(
            f"Пример результата для промта: {preset.prompt}\n\n"
            "✅ После выбора нужного промта, просто отправь мне фото 📎"
        ),
    )


def register(dp):
    dp.register_callback_query_handler(preset_callback, Text(startswith="preset:"))
