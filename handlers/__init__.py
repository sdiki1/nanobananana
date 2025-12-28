from handlers import admin, generation, menu, models, payments, presets, start


def register_all(dp) -> None:
    start.register(dp)
    admin.register(dp)
    menu.register(dp)
    models.register(dp)
    presets.register(dp)
    payments.register(dp)
    generation.register(dp)
