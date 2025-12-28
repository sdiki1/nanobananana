import secrets
import string
from typing import Optional

def generate_referral_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def format_main_screen(user, veo_prompts_url: str, instruction_url: str) -> str:
    return (
        "✅ Нейросети — для генерации изображений по тексту.\n\n"
        f"Осталось генераций: 💎 {user.diamonds}\n"
        f"Осталось генераций NanoBanana: 🍌 {user.bananas}\n\n"
        f"<a href=\"{veo_prompts_url}\">@veo-prompts</a>\n\n"
        f"<a href=\"{instruction_url}\">📘 Инструкция — как пользоваться ботом</a>\n\n"
        "✍️ Напишите ваш запрос:"
    )


def format_profile(
    user,
    referrals_count: int,
    available_tokens: int,
) -> str:
    username = user.username or "—"
    return (
        "👤 Профиль\n\n"
        f"username: {username}\n"
        f"tg_id: {user.tg_id}\n"
        f"referrals_count: {referrals_count}\n"
        f"earned_usdt: {user.earned_usdt}\n"
        f"usdt_balance: {user.usdt_balance}\n"
        f"available_tokens: {available_tokens}"
    )


def make_ref_link(bot_username: Optional[str], ref_code: str) -> str:
    if not bot_username:
        return f"https://t.me/your_bot?start=ref_{ref_code}"
    return f"https://t.me/{bot_username}?start=ref_{ref_code}"
