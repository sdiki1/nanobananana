from decimal import Decimal

from aiogram import types
from aiogram.dispatcher.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.repositories import adjust_balances, confirm_topup, create_transaction, find_user, get_user_by_tg_id


def _is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


async def admin_help(message: types.Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    await message.answer(
        "/admin_add <tg_id> <diamonds> <bananas>\n"
        "/admin_sub <tg_id> <diamonds> <bananas>\n"
        "/admin_find <tg_id|username>\n"
        "/confirm_order <order_id>"
    )


async def admin_add(message: types.Message, session: AsyncSession) -> None:
    if not _is_admin(message.from_user.id):
        return
    parts = message.get_args().split()
    if len(parts) < 3:
        await message.answer("Использование: /admin_add <tg_id> <diamonds> <bananas>")
        return
    tg_id, diamonds, bananas = parts[0], int(parts[1]), int(parts[2])
    user = await get_user_by_tg_id(session, int(tg_id))
    if not user:
        await message.answer("Пользователь не найден")
        return
    await adjust_balances(session, user.id, diamonds_delta=diamonds, bananas_delta=bananas)
    await create_transaction(
        session,
        user_id=user.id,
        tx_type="admin_adjust",
        status="paid",
        amount_diamonds=diamonds,
        amount_bananas=bananas,
        amount_usdt=Decimal("0"),
        payload={"admin_id": message.from_user.id},
    )
    await message.answer("Баланс обновлен")


async def admin_sub(message: types.Message, session: AsyncSession) -> None:
    if not _is_admin(message.from_user.id):
        return
    parts = message.get_args().split()
    if len(parts) < 3:
        await message.answer("Использование: /admin_sub <tg_id> <diamonds> <bananas>")
        return
    tg_id, diamonds, bananas = parts[0], int(parts[1]), int(parts[2])
    user = await get_user_by_tg_id(session, int(tg_id))
    if not user:
        await message.answer("Пользователь не найден")
        return
    if user.diamonds < diamonds or user.bananas < bananas:
        await message.answer("Недостаточно токенов для списания")
        return
    await adjust_balances(session, user.id, diamonds_delta=-diamonds, bananas_delta=-bananas)
    await create_transaction(
        session,
        user_id=user.id,
        tx_type="admin_adjust",
        status="paid",
        amount_diamonds=-diamonds,
        amount_bananas=-bananas,
        amount_usdt=Decimal("0"),
        payload={"admin_id": message.from_user.id},
    )
    await message.answer("Баланс обновлен")


async def admin_find(message: types.Message, session: AsyncSession) -> None:
    if not _is_admin(message.from_user.id):
        return
    query = message.get_args().strip()
    if not query:
        await message.answer("Использование: /admin_find <tg_id|username>")
        return
    user = await find_user(session, query)
    if not user:
        await message.answer("Пользователь не найден")
        return
    await message.answer(
        "Пользователь найден:\n"
        f"tg_id: {user.tg_id}\n"
        f"username: {user.username}\n"
        f"diamonds: {user.diamonds}\n"
        f"bananas: {user.bananas}"
    )


async def confirm_order(message: types.Message, session: AsyncSession) -> None:
    if not _is_admin(message.from_user.id):
        return
    order_id = message.get_args().strip()
    if not order_id:
        await message.answer("Использование: /confirm_order <order_id>")
        return
    tx = await confirm_topup(session, order_id)
    if not tx:
        await message.answer("Заказ не найден или уже обработан")
        return
    await message.answer("Заказ подтвержден, токены начислены")


def register(dp):
    dp.register_message_handler(admin_help, Command("admin"))
    dp.register_message_handler(admin_add, Command("admin_add"))
    dp.register_message_handler(admin_sub, Command("admin_sub"))
    dp.register_message_handler(admin_find, Command("admin_find"))
    dp.register_message_handler(confirm_order, Command("confirm_order"))
