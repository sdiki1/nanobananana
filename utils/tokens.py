from typing import Optional, Tuple

from utils.constants import MODEL_PRICES


def select_token_cost(user, model: str) -> Optional[Tuple[int, int]]:
    price = MODEL_PRICES.get(model, 1)
    if model == "nano":
        if user.bananas >= price:
            return 0, price
        if user.diamonds >= price:
            return price, 0
        return None
    if user.diamonds >= price:
        return price, 0
    return None
