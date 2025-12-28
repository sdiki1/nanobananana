from __future__ import annotations

MODEL_NAMES = {
    "nano": "Nano",
    "pro": "Pro",
}

MODEL_PRICES = {
    "nano": 1,
    "pro": 2,
}

BTN_MODEL_TEMPLATE = "🧠 Модель: {model_name} 🔽"
BTN_ANIMATE = "🎥 Оживить фото"
BTN_PRESETS = "Готовые промпты (в 1 клик)"
BTN_TOPUP = "💳 Пополнить баланс"
BTN_SUPPORT = "🧑‍💻 Поддержка ↗"
BTN_PROFILE = "👤 Профиль"
BTN_REFERRAL = "🧑‍🤝‍🧑 Реферальная программа"
BTN_BACK = "⬅ Назад"
BTN_RESET_PRESET = "❌ Сброс"
BTN_BUY_TOKENS = "Купить токены"

PROFILE_MENU_BUTTONS = [
    BTN_ANIMATE,
    BTN_BUY_TOKENS,
    BTN_REFERRAL,
    BTN_BACK,
]

ANIMATE_WARNINGS = [
    "⚠️ Время обработки может занять до нескольких минут.",
    "⚠️ Лучший результат получается на крупном плане лица.",
    "⚠️ Итоговое видео может отличаться от исходного фото.",
]

MAIN_MENU_BUTTONS = [
    BTN_ANIMATE,
    BTN_PRESETS,
    BTN_TOPUP,
    BTN_SUPPORT,
    BTN_PROFILE,
    BTN_REFERRAL,
]
