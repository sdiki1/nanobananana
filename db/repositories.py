from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.models import ActionLog, Generation, Referral, Transaction, User
from utils.helpers import generate_referral_code


async def get_user_by_tg_id(session: AsyncSession, tg_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    return result.scalar_one_or_none()


async def get_user_by_ref_code(session: AsyncSession, ref_code: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.referral_code == ref_code))
    return result.scalar_one_or_none()


async def get_or_create_user(
    session: AsyncSession,
    tg_id: int,
    username: Optional[str],
    ref_code: Optional[str] = None,
) -> User:
    user = await get_user_by_tg_id(session, tg_id)
    if user:
        if username and user.username != username:
            user.username = username
            await session.commit()
        return user

    referrer_id = None
    if ref_code:
        referrer = await get_user_by_ref_code(session, ref_code)
        if referrer and referrer.tg_id != tg_id:
            referrer_id = referrer.id

    referral_code = await _generate_unique_ref_code(session)
    user = User(
        tg_id=tg_id,
        username=username,
        referral_code=referral_code,
        referrer_id=referrer_id,
    )
    session.add(user)
    await session.flush()

    if referrer_id:
        session.add(Referral(referrer_id=referrer_id, referred_user_id=user.id))

    await session.commit()
    return user


async def _generate_unique_ref_code(session: AsyncSession) -> str:
    while True:
        code = generate_referral_code()
        result = await session.execute(select(User).where(User.referral_code == code))
        if result.scalar_one_or_none() is None:
            return code


async def set_user_model(session: AsyncSession, user_id: int, model: str) -> None:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    user.selected_model = model
    await session.commit()


async def set_user_preset(session: AsyncSession, user_id: int, preset: Optional[str]) -> None:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    user.selected_preset = preset
    await session.commit()


async def adjust_balances(
    session: AsyncSession,
    user_id: int,
    diamonds_delta: int = 0,
    bananas_delta: int = 0,
    usdt_delta: Decimal = Decimal("0"),
    earned_usdt_delta: Decimal = Decimal("0"),
) -> User:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    user.diamonds += diamonds_delta
    user.bananas += bananas_delta
    user.usdt_balance += usdt_delta
    user.earned_usdt += earned_usdt_delta
    await session.commit()
    return user


async def create_generation(
    session: AsyncSession,
    user_id: int,
    kind: str,
    model: Optional[str],
    prompt: Optional[str],
    preset: Optional[str],
    cost_diamonds: int = 0,
    cost_bananas: int = 0,
) -> Generation:
    generation = Generation(
        user_id=user_id,
        kind=kind,
        model=model,
        prompt=prompt,
        preset=preset,
        cost_diamonds=cost_diamonds,
        cost_bananas=cost_bananas,
        status="processing",
    )
    session.add(generation)
    await session.commit()
    return generation


async def update_generation_status(
    session: AsyncSession,
    generation_id: int,
    status: str,
    result_url: Optional[str] = None,
    error: Optional[str] = None,
) -> None:
    result = await session.execute(select(Generation).where(Generation.id == generation_id))
    generation = result.scalar_one()
    generation.status = status
    generation.result_url = result_url
    generation.error = error
    await session.commit()


async def create_transaction(
    session: AsyncSession,
    user_id: int,
    tx_type: str,
    method: Optional[str] = None,
    status: str = "pending",
    amount_diamonds: int = 0,
    amount_bananas: int = 0,
    amount_usdt: Decimal = Decimal("0"),
    external_id: Optional[str] = None,
    payload: Optional[dict] = None,
) -> Transaction:
    tx = Transaction(
        user_id=user_id,
        type=tx_type,
        method=method,
        status=status,
        amount_diamonds=amount_diamonds,
        amount_bananas=amount_bananas,
        amount_usdt=amount_usdt,
        external_id=external_id,
        payload=payload,
    )
    session.add(tx)
    await session.commit()
    return tx


async def get_transaction_by_external_id(session: AsyncSession, external_id: str) -> Optional[Transaction]:
    result = await session.execute(select(Transaction).where(Transaction.external_id == external_id))
    return result.scalar_one_or_none()


async def confirm_topup(session: AsyncSession, external_id: str) -> Optional[Transaction]:
    tx = await get_transaction_by_external_id(session, external_id)
    if not tx or tx.status != "pending":
        return None

    result = await session.execute(select(User).where(User.id == tx.user_id))
    user = result.scalar_one()
    user.diamonds += tx.amount_diamonds
    user.bananas += tx.amount_bananas
    tx.status = "paid"

    if user.referrer_id:
        percent = Decimal(str(settings.referral_percent))
        bonus_usdt = (Decimal(tx.amount_diamonds) * percent) / Decimal("100")
        bonus_usdt = bonus_usdt.quantize(Decimal("0.01"))
        ref_result = await session.execute(select(User).where(User.id == user.referrer_id))
        referrer = ref_result.scalar_one()
        referrer.usdt_balance += bonus_usdt
        referrer.earned_usdt += bonus_usdt
        session.add(
            Transaction(
                user_id=referrer.id,
                type="referral_bonus",
                method=tx.method,
                status="paid",
                amount_usdt=bonus_usdt,
                payload={"source_tx": tx.external_id},
            )
        )

    await session.commit()
    return tx


async def get_referrals_count(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(select(Referral).where(Referral.referrer_id == user_id))
    return len(result.scalars().all())


async def find_user(session: AsyncSession, query: str) -> Optional[User]:
    if query.isdigit():
        result = await session.execute(select(User).where(User.tg_id == int(query)))
        return result.scalar_one_or_none()
    result = await session.execute(select(User).where(User.username == query))
    return result.scalar_one_or_none()


async def log_action(
    session: AsyncSession,
    tg_id: int,
    username: Optional[str],
    action: str,
    payload: Optional[dict] = None,
) -> ActionLog:
    entry = ActionLog(tg_id=tg_id, username=username, action=action, payload=payload)
    session.add(entry)
    await session.commit()
    return entry


async def get_action_logs(session: AsyncSession, limit: int = 1000) -> list[ActionLog]:
    result = await session.execute(select(ActionLog).order_by(ActionLog.created_at.desc()).limit(limit))
    return list(result.scalars().all())
