import uuid

from aiogram import types
from aiogram.dispatcher.filters import Text
from aiogram.types import ContentType
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.repositories import confirm_topup, create_transaction, get_user_by_tg_id
from handlers.common import send_main_menu
from keyboards.main import card_packages_kb, stars_packages_kb, topup_method_kb
from services.payments.card import CardPaymentService
from services.payments.stars import StarsPaymentService
from utils.pricing import get_card_package, get_stars_package


card_service = CardPaymentService()
stars_service = StarsPaymentService()


async def topup_callback(query: types.CallbackQuery, session: AsyncSession) -> None:
    action = query.data.split(":", 1)[1]
    if action == "card":
        await query.message.edit_text("Выберите пакет Card RUB:")
        await query.message.edit_reply_markup(reply_markup=card_packages_kb())
        await query.answer()
        return
    if action == "stars":
        await query.message.edit_text("Выберите пакет Telegram Stars:")
        await query.message.edit_reply_markup(reply_markup=stars_packages_kb())
        await query.answer()
        return
    if action == "back":
        user = await get_user_by_tg_id(session, query.from_user.id)
        if user:
            await send_main_menu(query.message, user, edit=True)
        else:
            await query.message.edit_text("Сначала отправьте /start")
        await query.answer()


async def card_callback(query: types.CallbackQuery, session: AsyncSession) -> None:
    code = query.data.split(":", 1)[1]
    if code == "back":
        await query.message.edit_text("Выберите способ оплаты:")
        await query.message.edit_reply_markup(reply_markup=topup_method_kb())
        await query.answer()
        return
    pkg = get_card_package(code)
    if not pkg:
        await query.answer("Пакет не найден", show_alert=True)
        return

    user = await get_user_by_tg_id(session, query.from_user.id)
    if not user:
        await query.answer("Сначала /start", show_alert=True)
        return

    link = card_service.create_payment_link(pkg, user.id)
    await create_transaction(
        session,
        user_id=user.id,
        tx_type="topup",
        method="card",
        status="pending",
        amount_diamonds=pkg.diamonds,
        external_id=link.order_id,
        payload={"package": pkg.code, "price_rub": pkg.price_rub},
    )

    await query.message.edit_text(
        "Оплатите заказ по ссылке:\n"
        f"{link.payment_url}\n\n"
        f"Номер заказа: {link.order_id}",
        disable_web_page_preview=True,
    )
    await query.message.edit_reply_markup(reply_markup=None)
    await query.answer("Ссылка отправлена")


async def stars_callback(query: types.CallbackQuery, session: AsyncSession) -> None:
    code = query.data.split(":", 1)[1]
    if code == "back":
        await query.message.edit_text("Выберите способ оплаты:")
        await query.message.edit_reply_markup(reply_markup=topup_method_kb())
        await query.answer()
        return
    pkg = get_stars_package(code)
    if not pkg:
        await query.answer("Пакет не найден", show_alert=True)
        return

    user = await get_user_by_tg_id(session, query.from_user.id)
    if not user:
        await query.answer("Сначала /start", show_alert=True)
        return

    order_id = f"STR-{uuid.uuid4().hex[:10]}"
    await create_transaction(
        session,
        user_id=user.id,
        tx_type="topup",
        method="stars",
        status="pending",
        amount_diamonds=pkg.diamonds,
        external_id=order_id,
        payload={"package": pkg.code, "stars": pkg.stars},
    )

    await stars_service.send_invoice(
        bot=query.bot,
        chat_id=query.message.chat.id,
        package=pkg,
        payload=order_id,
        provider_token=settings.stars_provider_token,
    )
    await query.message.edit_text("Счёт в Telegram Stars отправлен. Оплатите его в чате.")
    await query.message.edit_reply_markup(reply_markup=None)
    await query.answer()


async def pre_checkout(pre_checkout_query: types.PreCheckoutQuery) -> None:
    await pre_checkout_query.bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


async def successful_payment(message: types.Message, session: AsyncSession) -> None:
    payload = message.successful_payment.invoice_payload
    tx = await confirm_topup(session, payload)
    if not tx:
        await message.answer("Платеж не найден или уже обработан.")
        return
    await message.answer("Платеж принят ✅ Токены начислены.")


def register(dp):
    dp.register_callback_query_handler(topup_callback, Text(startswith="topup:"))
    dp.register_callback_query_handler(card_callback, Text(startswith="card:"))
    dp.register_callback_query_handler(stars_callback, Text(startswith="stars:"))
    dp.register_pre_checkout_query_handler(pre_checkout)
    dp.register_message_handler(successful_payment, content_types=ContentType.SUCCESSFUL_PAYMENT)
