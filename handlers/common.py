from aiogram import types
from aiogram.types import ParseMode

from config import settings
from keyboards.main import main_menu_kb
from utils.helpers import format_main_screen


async def send_main_menu(message: types.Message, user, *, edit: bool = False) -> None:
    text = format_main_screen(user, settings.veo_prompts_url, settings.instruction_url)
    if edit:
        await message.edit_text(
            text,
            reply_markup=main_menu_kb(user.selected_model),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return
    await message.answer(
        text,
        reply_markup=main_menu_kb(user.selected_model),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
