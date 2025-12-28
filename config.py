import os
from dataclasses import dataclass
from typing import Optional, Set

from dotenv import load_dotenv

load_dotenv()


def _get_env(key: str, default: Optional[str] = None) -> str:
    value = os.getenv(key, default)
    if value is None:
        raise RuntimeError(f"Missing required env var: {key}")
    return value


def _get_int_env(key: str, default: Optional[int] = None) -> int:
    value = os.getenv(key)
    if value is None:
        if default is None:
            raise RuntimeError(f"Missing required env var: {key}")
        return default
    return int(value)


def _get_float_env(key: str, default: Optional[float] = None) -> float:
    value = os.getenv(key)
    if value is None:
        if default is None:
            raise RuntimeError(f"Missing required env var: {key}")
        return default
    return float(value)


def _get_admin_ids() -> Set[int]:
    raw = os.getenv("ADMIN_IDS", "")
    ids = set()
    for part in raw.split(","):
        part = part.strip()
        if part:
            ids.add(int(part))
    return ids


@dataclass(frozen=True)
class Settings:
    bot_token: str
    bot_username: Optional[str]
    database_url: str
    admin_ids: Set[int]
    support_url: str
    instruction_url: str
    veo_prompts_url: str
    chatgpt_url: str
    veo_url: str
    referral_percent: float
    animate_cost: int
    stars_provider_token: str
    fsm_storage: str
    redis_url: Optional[str]
    yoomoney_base_url: str

    @staticmethod
    def load() -> "Settings":
        return Settings(
            bot_token=_get_env("BOT_TOKEN"),
            bot_username=os.getenv("BOT_USERNAME"),
            database_url=_get_env("DATABASE_URL"),
            admin_ids=_get_admin_ids(),
            support_url=_get_env("SUPPORT_URL", "https://t.me/support"),
            instruction_url=_get_env("INSTRUCTION_URL", "https://example.com/instruction"),
            veo_prompts_url=_get_env("VEO_PROMPTS_URL", "https://t.me/veo-prompts"),
            chatgpt_url=_get_env("CHATGPT_URL", "https://t.me/"),
            veo_url=_get_env("VEO_URL", "https://t.me/"),
            referral_percent=_get_float_env("REFERRAL_PERCENT", 10.0),
            animate_cost=_get_int_env("ANIMATE_COST", 5),
            stars_provider_token=os.getenv("STARS_PROVIDER_TOKEN", ""),
            fsm_storage=os.getenv("FSM_STORAGE", "memory"),
            redis_url=os.getenv("REDIS_URL"),
            yoomoney_base_url=_get_env("YOOMONEY_BASE_URL", "https://pay.nanobanana.mock"),
        )


settings = Settings.load()
