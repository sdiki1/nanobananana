from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    diamonds = Column(Integer, nullable=False, default=0)
    bananas = Column(Integer, nullable=False, default=0)
    usdt_balance = Column(Numeric(14, 2), nullable=False, default=0)
    earned_usdt = Column(Numeric(14, 2), nullable=False, default=0)
    referral_code = Column(String(32), unique=True, nullable=False)
    referrer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    selected_model = Column(String(16), nullable=False, default="nano")
    selected_preset = Column(String(64))

    referrer = relationship("User", remote_side=[id], backref="referrals")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(32), nullable=False)
    method = Column(String(32))
    status = Column(String(32), nullable=False, default="pending")
    amount_diamonds = Column(Integer, nullable=False, default=0)
    amount_bananas = Column(Integer, nullable=False, default=0)
    amount_usdt = Column(Numeric(14, 2), nullable=False, default=0)
    external_id = Column(String(128))
    payload = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")


class Generation(Base):
    __tablename__ = "generations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    kind = Column(String(32), nullable=False)
    model = Column(String(16))
    prompt = Column(Text)
    preset = Column(String(64))
    status = Column(String(32), nullable=False, default="processing")
    cost_diamonds = Column(Integer, nullable=False, default=0)
    cost_bananas = Column(Integer, nullable=False, default=0)
    result_url = Column(Text)
    error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True)
    referrer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    referred_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    referrer = relationship("User", foreign_keys=[referrer_id])
    referred_user = relationship("User", foreign_keys=[referred_user_id])
