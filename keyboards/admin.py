from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_main_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(text="🔍 Найти пользователя", callback_data="admin:find"))
    kb.add(InlineKeyboardButton(text="➕ Начислить токены", callback_data="admin:add"))
    kb.add(InlineKeyboardButton(text="➖ Списать токены", callback_data="admin:sub"))
    kb.add(InlineKeyboardButton(text="📄 Выгрузить логи", callback_data="admin:export"))
    return kb


def admin_user_kb(tg_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text="➕ Начислить", callback_data=f"admin:user:add:{tg_id}"),
        InlineKeyboardButton(text="➖ Списать", callback_data=f"admin:user:sub:{tg_id}"),
    )
    kb.add(InlineKeyboardButton(text="⬅ В меню", callback_data="admin:menu"))
    return kb
