from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.repositories import get_referrals_count, get_user_by_tg_id
from handlers.generation import start_animate_callback
from handlers.common import send_main_menu
from keyboards.main import link_inline_kb, model_select_kb, presets_kb, profile_menu_kb, topup_method_kb
from utils.helpers import format_profile, make_ref_link


async def show_model_select(query: types.CallbackQuery, session: AsyncSession) -> None:
    user = await get_user_by_tg_id(session, query.from_user.id)
    if not user:
        await query.message.answer("Сначала отправьте /start")
        return
    await query.message.answer("Выберите модель:", reply_markup=model_select_kb(user.selected_model))


async def show_presets(query: types.CallbackQuery, session: AsyncSession) -> None:
    user = await get_user_by_tg_id(session, query.from_user.id)
    if not user:
        await query.message.answer("Сначала отправьте /start")
        return
    await query.message.answer("Выберите пресет:", reply_markup=presets_kb(user.selected_preset))


async def show_topup(query: types.CallbackQuery) -> None:
    await query.message.answer("Выберите способ оплаты:", reply_markup=topup_method_kb())


async def show_support(query: types.CallbackQuery) -> None:
    await query.message.answer(
        "Свяжитесь с поддержкой:",
        reply_markup=link_inline_kb("🧑‍💻 Поддержка", settings.support_url),
    )


async def show_profile(query: types.CallbackQuery, session: AsyncSession) -> None:
    user = await get_user_by_tg_id(session, query.from_user.id)
    if not user:
        await query.message.answer("Сначала отправьте /start")
        return

    referrals_count = await get_referrals_count(session, user.id)
    available_tokens = user.diamonds + user.bananas
    text = format_profile(user, referrals_count, available_tokens)
    await query.message.answer(text, reply_markup=profile_menu_kb())


async def show_referral(query: types.CallbackQuery, session: AsyncSession) -> None:
    user = await get_user_by_tg_id(session, query.from_user.id)
    if not user:
        await query.message.answer("Сначала отправьте /start")
        return
    bot_username = settings.bot_username
    if not bot_username:
        me = await query.bot.get_me()
        bot_username = me.username
    ref_link = make_ref_link(bot_username, user.referral_code)
    await query.message.answer(
        "🧑‍🤝‍🧑 Реферальная программа\n\n"
        f"Ваша ссылка: <a href=\"{ref_link}\">{ref_link}</a>\n"
        f"Процент вознаграждения: {settings.referral_percent}%",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


async def back_to_main(query: types.CallbackQuery, session: AsyncSession) -> None:
    user = await get_user_by_tg_id(session, query.from_user.id)
    if not user:
        await query.message.answer("Сначала отправьте /start")
        return
    await send_main_menu(query.message, user)


async def menu_callback(query: types.CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    action = query.data.split(":", 1)[1]
    if action == "model":
        await show_model_select(query, session)
    elif action == "animate":
        await start_animate_callback(query, state, session)
    elif action == "presets":
        await show_presets(query, session)
    elif action == "topup":
        await show_topup(query)
    elif action == "support":
        await show_support(query)
    elif action == "profile":
        await show_profile(query, session)
    elif action == "referral":
        await show_referral(query, session)
    elif action == "back":
        await back_to_main(query, session)
    await query.answer()


def register(dp):
    dp.register_callback_query_handler(menu_callback, lambda c: c.data and c.data.startswith("menu:"))
