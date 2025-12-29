import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

from config import settings
from db.session import create_engine, create_session_factory
from handlers import register_all
from middlewares.db import DBSessionMiddleware
from middlewares.action_logger import ActionLoggingMiddleware


logging.basicConfig(level=logging.INFO)


def _build_storage():
    if settings.fsm_storage == "redis" and settings.redis_url:
        try:
            from aiogram.contrib.fsm_storage.redis import RedisStorage2
        except ImportError:  # pragma: no cover - optional dependency
            logging.warning("Redis storage requested but aioredis is not installed. Using memory storage.")
            return MemoryStorage()
        return RedisStorage2.from_url(settings.redis_url)
    return MemoryStorage()


def main() -> None:
    storage = _build_storage()
    bot = Bot(token=settings.bot_token, parse_mode="HTML")
    dp = Dispatcher(bot, storage=storage)

    engine = create_engine()
    session_factory = create_session_factory(engine)
    dp.middleware.setup(DBSessionMiddleware(session_factory))
    dp.middleware.setup(ActionLoggingMiddleware(session_factory))

    register_all(dp)

    executor.start_polling(dp, skip_updates=True)


if __name__ == "__main__":
    main()
