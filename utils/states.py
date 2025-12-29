from aiogram.dispatcher.filters.state import State, StatesGroup


class GenerationStates(StatesGroup):
    waiting_photo_animate = State()
    waiting_photo_preset = State()


class AdminStates(StatesGroup):
    waiting_user_query = State()
    waiting_amounts = State()
