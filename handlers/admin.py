from decimal import Decimal

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.repositories import (
    adjust_balances,
    confirm_topup,
    create_transaction,
    find_user,
    get_referrals_count,
    get_action_logs,
    get_user_by_tg_id,
    log_action,
)
from keyboards.admin import admin_main_kb, admin_user_kb
from utils.states import AdminStates
from utils.helpers import format_profile


def _is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


async def admin_help(message: types.Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    await message.answer("Админ-панель", reply_markup=admin_main_kb())


async def admin_add(message: types.Message, session: AsyncSession) -> None:
    if not _is_admin(message.from_user.id):
        return
    await message.answer("Баланс обновление стартовано...")
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


async def admin_panel(message: types.Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return
    await state.finish()
    await message.answer("Админ-панель", reply_markup=admin_main_kb())


async def _prompt_user_query(target, state: FSMContext, operation: str):
    await state.finish()
    await state.update_data(operation=operation)
    await state.set_state(AdminStates.waiting_user_query.state)
    await target.edit_text("Введите tg_id или username пользователя")


async def _export_logs(message: types.Message, session: AsyncSession) -> None:
    logs = await get_action_logs(session)
    if not logs:
        await message.answer("Логи пустые.")
        return
    import csv
    import io
    from aiogram.types import InputFile
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "tg_id", "username", "action", "payload", "created_at"])
    for entry in reversed(logs):
        writer.writerow(
            [
                entry.id,
                entry.tg_id,
                entry.username or "",
                entry.action,
                entry.payload,
                entry.created_at,
            ]
        )
    buffer.seek(0)
    await message.answer_document(InputFile(io.BytesIO(buffer.read().encode("utf-8")), filename="action_logs.csv"))


async def admin_callback(query: types.CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    if not _is_admin(query.from_user.id):
        await query.answer("Нет доступа", show_alert=True)
        return
    action = query.data.split(":", 1)[1]
    if action == "menu":
        await state.finish()
        await query.message.edit_text("Админ-панель", reply_markup=admin_main_kb())
        await query.answer()
        return
    if action in {"find", "add", "sub"}:
        await _prompt_user_query(query.message, state, action)
        await query.answer()
        return
    if action == "export":
        await _export_logs(query.message, session)
        await query.answer("Готово")
        return
    await query.answer()


async def admin_user_action(query: types.CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    if not _is_admin(query.from_user.id):
        await query.answer("Нет доступа", show_alert=True)
        return
    _, _, op, tg_id_str = query.data.split(":", 3)
    tg_id = int(tg_id_str)
    await state.finish()
    await state.update_data(operation=op, target_tg_id=tg_id)
    await state.set_state(AdminStates.waiting_amounts.state)
    await query.message.edit_text("Введите через пробел: diamonds bananas", parse_mode=None)
    await query.answer()


async def admin_user_query_input(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    if not _is_admin(message.from_user.id):
        return
    data = await state.get_data()
    operation = data.get("operation")
    if not operation:
        await message.answer("Выберите действие через /admin")
        await state.finish()
        return
    user = await find_user(session, message.text.strip())
    if not user:
        await message.answer("Пользователь не найден, попробуйте ещё раз.")
        return
    await state.update_data(target_tg_id=user.tg_id)
    if operation == "find":
        referrals = await get_referrals_count(session, user.id)
        info = format_profile(user, referrals_count=referrals, available_tokens=user.diamonds + user.bananas)
        await message.answer(f"Пользователь:\n{info}", reply_markup=admin_user_kb(user.tg_id))
        await state.finish()
        return
    await state.set_state(AdminStates.waiting_amounts.state)
    action_word = "начислить" if operation == "add" else "списать"
    await message.answer(
        f"Пользователь найден: tg_id={user.tg_id}, username={user.username}\n"
        f"Текущий баланс: 💎 {user.diamonds}, 🍌 {user.bananas}\n"
        f"Введите сколько {action_word}: diamonds bananas",
        parse_mode=None,
    )


async def admin_amounts_input(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    if not _is_admin(message.from_user.id):
        return
    data = await state.get_data()
    operation = data.get("operation")
    target_tg_id = data.get("target_tg_id")
    if not operation or not target_tg_id:
        await message.answer("Сначала выберите пользователя через админ-панель.")
        await state.finish()
        return
    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.answer("Нужно два числа: <diamonds> <bananas>")
        return
    try:
        diamonds = int(parts[0])
        bananas = int(parts[1])
    except ValueError:
        await message.answer("Значения должны быть числами.")
        return
    user = await get_user_by_tg_id(session, target_tg_id)
    if not user:
        await message.answer("Пользователь не найден.")
        await state.finish()
        return
    if operation == "sub":
        if user.diamonds < diamonds or user.bananas < bananas:
            await message.answer("Недостаточно токенов для списания.")
            return
        diamonds_delta = -diamonds
        bananas_delta = -bananas
    else:
        diamonds_delta = diamonds
        bananas_delta = bananas
    updated_user = await adjust_balances(session, user.id, diamonds_delta=diamonds_delta, bananas_delta=bananas_delta)
    await create_transaction(
        session,
        user_id=user.id,
        tx_type="admin_adjust",
        status="paid",
        amount_diamonds=diamonds_delta,
        amount_bananas=bananas_delta,
        amount_usdt=Decimal("0"),
        payload={"admin_id": message.from_user.id},
    )
    await log_action(
        session,
        tg_id=message.from_user.id,
        username=message.from_user.username,
        action="admin_adjust",
        payload={
            "target_tg_id": user.tg_id,
            "diamonds_delta": diamonds_delta,
            "bananas_delta": bananas_delta,
        },
    )
    await message.answer(
        f"Баланс обновлён. Теперь: 💎 {updated_user.diamonds}, 🍌 {updated_user.bananas}",
        reply_markup=admin_main_kb(),
    )
    await state.finish()


def register(dp):
    dp.register_message_handler(admin_help, Command("admin"))
    dp.register_message_handler(admin_add, Command("admin_add"))
    dp.register_message_handler(admin_sub, Command("admin_sub"))
    dp.register_message_handler(admin_find, Command("admin_find"))
    dp.register_message_handler(confirm_order, Command("confirm_order"))
    dp.register_message_handler(admin_panel, Command("admin_panel"), state="*")
    dp.register_callback_query_handler(admin_user_action, Text(startswith="admin:user:"), state="*")
    dp.register_callback_query_handler(admin_callback, Text(startswith="admin:"), state="*")
    dp.register_message_handler(admin_user_query_input, state=AdminStates.waiting_user_query)
    dp.register_message_handler(admin_amounts_input, state=AdminStates.waiting_amounts)
