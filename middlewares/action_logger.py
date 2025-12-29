import logging

from aiogram.dispatcher.middlewares import BaseMiddleware

from db.repositories import log_action


logger = logging.getLogger(__name__)


class ActionLoggingMiddleware(BaseMiddleware):
    def __init__(self, session_factory):
        super().__init__()
        self.session_factory = session_factory

    async def on_post_process_message(self, message, results, data):
        await self._log_message(message)

    async def on_post_process_callback_query(self, callback_query, results, data):
        await self._log_callback(callback_query)

    async def on_post_process_pre_checkout_query(self, pre_checkout_query, results, data):
        await self._log_pre_checkout(pre_checkout_query)

    async def on_post_process_successful_payment(self, message, results, data):
        await self._log_message(message, action_override="payment")

    async def _log_message(self, message, action_override: Optional[str] = None):
        session = self.session_factory()
        try:
            action = action_override or f"message:{message.content_type}"
            payload = {
                "message_id": message.message_id,
                "chat_id": message.chat.id,
                "text": message.text,
                "caption": getattr(message, "caption", None),
                "content_type": message.content_type,
            }
            if message.content_type == "photo" and message.photo:
                payload["file_id"] = message.photo[-1].file_id
            if message.content_type == "document" and message.document:
                payload["file_id"] = message.document.file_id
            await log_action(
                session,
                tg_id=message.from_user.id,
                username=message.from_user.username,
                action=action,
                payload=payload,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to log message action: %s", exc)
        finally:
            await session.close()

    async def _log_callback(self, query):
        session = self.session_factory()
        try:
            payload = {
                "data": query.data,
                "message_id": query.message.message_id if query.message else None,
                "chat_id": query.message.chat.id if query.message else None,
            }
            await log_action(
                session,
                tg_id=query.from_user.id,
                username=query.from_user.username,
                action="callback",
                payload=payload,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to log callback action: %s", exc)
        finally:
            await session.close()

    async def _log_pre_checkout(self, pre_checkout_query):
        session = self.session_factory()
        try:
            payload = {
                "currency": pre_checkout_query.currency,
                "total_amount": pre_checkout_query.total_amount,
                "invoice_payload": pre_checkout_query.invoice_payload,
            }
            await log_action(
                session,
                tg_id=pre_checkout_query.from_user.id,
                username=pre_checkout_query.from_user.username,
                action="pre_checkout",
                payload=payload,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to log pre_checkout action: %s", exc)
        finally:
            await session.close()
