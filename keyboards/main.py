from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils.constants import (
    BTN_ANIMATE,
    BTN_BACK,
    BTN_BUY_TOKENS,
    BTN_MODEL_TEMPLATE,
    BTN_PRESETS,
    BTN_PROFILE,
    BTN_REFERRAL,
    BTN_RESET_PRESET,
    BTN_SUPPORT,
    BTN_TOPUP,
    MODEL_NAMES,
    MODEL_PRICES,
    PROFILE_MENU_BUTTONS,
)
from utils.presets import list_presets
from utils.pricing import list_card_packages, list_stars_packages


def main_menu_kb(model_key: str) -> InlineKeyboardMarkup:
    model_name = MODEL_NAMES.get(model_key, "Nano")
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(
            text=BTN_MODEL_TEMPLATE.format(model_name=model_name),
            callback_data="menu:model",
        )
    )
    kb.add(InlineKeyboardButton(text=BTN_ANIMATE, callback_data="menu:animate"))
    kb.add(InlineKeyboardButton(text=BTN_PRESETS, callback_data="menu:presets"))
    kb.add(InlineKeyboardButton(text=BTN_TOPUP, callback_data="menu:topup"))
    kb.row(
        InlineKeyboardButton(text=BTN_SUPPORT, callback_data="menu:support"),
        InlineKeyboardButton(text=BTN_PROFILE, callback_data="menu:profile"),
    )
    kb.add(InlineKeyboardButton(text=BTN_REFERRAL, callback_data="menu:referral"))
    return kb


def profile_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton(text=PROFILE_MENU_BUTTONS[0], callback_data="menu:animate"))
    kb.add(InlineKeyboardButton(text=PROFILE_MENU_BUTTONS[1], callback_data="menu:topup"))
    kb.add(InlineKeyboardButton(text=PROFILE_MENU_BUTTONS[2], callback_data="menu:referral"))
    kb.add(InlineKeyboardButton(text=PROFILE_MENU_BUTTONS[3], callback_data="menu:back"))
    return kb


def model_select_kb(selected_model: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    for key in ("nano", "pro"):
        title = MODEL_NAMES.get(key, key)
        price = MODEL_PRICES.get(key, 1)
        prefix = "✅ " if key == selected_model else ""
        kb.insert(
            InlineKeyboardButton(
                text=f"{prefix}{title} ({price})",
                callback_data=f"model:{key}",
            )
        )
    kb.add(InlineKeyboardButton(text=BTN_BACK, callback_data="model:back"))
    return kb


def presets_kb(selected_key: str | None = None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    for preset in list_presets():
        prefix = "✅ " if preset.key == selected_key else ""
        kb.insert(
            InlineKeyboardButton(
                text=f"{prefix}{preset.title}",
                callback_data=f"preset:{preset.key}",
            )
        )
    kb.add(InlineKeyboardButton(text=BTN_RESET_PRESET, callback_data="preset:reset"))
    kb.add(InlineKeyboardButton(text=BTN_BACK, callback_data="preset:back"))
    return kb


def topup_method_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(text="Card RUB", callback_data="topup:card"))
    kb.add(InlineKeyboardButton(text="Telegram Stars", callback_data="topup:stars"))
    kb.add(InlineKeyboardButton(text=BTN_BACK, callback_data="topup:back"))
    return kb


def card_packages_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    for pkg in list_card_packages():
        kb.insert(
            InlineKeyboardButton(
                text=f"{pkg.diamonds} 💎 — {pkg.price_rub} RUB",
                callback_data=f"card:{pkg.code}",
            )
        )
    kb.add(InlineKeyboardButton(text=BTN_BACK, callback_data="card:back"))
    return kb


def stars_packages_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    for pkg in list_stars_packages():
        kb.insert(
            InlineKeyboardButton(
                text=f"{pkg.diamonds} генераций — {pkg.stars} ⭐",
                callback_data=f"stars:{pkg.code}",
            )
        )
    kb.add(InlineKeyboardButton(text=BTN_BACK, callback_data="stars:back"))
    return kb


def link_inline_kb(title: str, url: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(text=title, url=url))
    return kb
