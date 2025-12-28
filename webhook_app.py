from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from db.repositories import confirm_topup
from db.session import create_engine, create_session_factory


app = FastAPI()
engine = create_engine()
session_factory = create_session_factory(engine)


class PaymentWebhook(BaseModel):
    order_id: str


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/payments/yoomoney")
async def yoomoney_webhook(payload: PaymentWebhook) -> dict:
    async with session_factory() as session:
        tx = await confirm_topup(session, payload.order_id)
    if not tx:
        raise HTTPException(status_code=404, detail="order not found")
    return {"status": "ok"}


@app.post("/payments/stars")
async def stars_webhook(payload: PaymentWebhook) -> dict:
    async with session_factory() as session:
        tx = await confirm_topup(session, payload.order_id)
    if not tx:
        raise HTTPException(status_code=404, detail="order not found")
    return {"status": "ok"}
