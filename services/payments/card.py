import uuid
from dataclasses import dataclass

from config import settings


@dataclass(frozen=True)
class CardPaymentLink:
    order_id: str
    payment_url: str


class CardPaymentService:
    def create_payment_link(self, package, user_id: int) -> CardPaymentLink:
        order_id = f"ORD-{uuid.uuid4().hex[:10]}"
        payment_url = f"{settings.yoomoney_base_url}/pay/{order_id}"
        return CardPaymentLink(order_id=order_id, payment_url=payment_url)
