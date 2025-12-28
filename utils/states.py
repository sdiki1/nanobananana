from aiogram.dispatcher.filters.state import State, StatesGroup


class GenerationStates(StatesGroup):
    waiting_photo_animate = State()
    waiting_photo_preset = State()
