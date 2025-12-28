from aiogram.dispatcher.middlewares import BaseMiddleware


class DBSessionMiddleware(BaseMiddleware):
    def __init__(self, session_factory):
        super().__init__()
        self.session_factory = session_factory

    async def on_pre_process_message(self, message, data):
        data["session"] = self.session_factory()

    async def on_post_process_message(self, message, results, data):
        session = data.get("session")
        if session:
            await session.close()

    async def on_pre_process_callback_query(self, callback_query, data):
        data["session"] = self.session_factory()

    async def on_post_process_callback_query(self, callback_query, results, data):
        session = data.get("session")
        if session:
            await session.close()

    async def on_pre_process_pre_checkout_query(self, pre_checkout_query, data):
        data["session"] = self.session_factory()

    async def on_post_process_pre_checkout_query(self, pre_checkout_query, results, data):
        session = data.get("session")
        if session:
            await session.close()

    async def on_pre_process_successful_payment(self, message, data):
        data["session"] = self.session_factory()

    async def on_post_process_successful_payment(self, message, results, data):
        session = data.get("session")
        if session:
            await session.close()
