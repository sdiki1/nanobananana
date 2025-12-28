from aiogram.types import LabeledPrice


class StarsPaymentService:
    async def send_invoice(self, bot, chat_id: int, package, payload: str, provider_token: str) -> None:
        title = f"{package.diamonds} генераций"
        description = f"Пакет на {package.diamonds} генераций"
        prices = [LabeledPrice(label=title, amount=package.stars)]
        await bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            currency="XTR",
            prices=prices,
            start_parameter="nanobanana",
        )
