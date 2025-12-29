# NanoBanana Bot (aiogram 2.7)

Telegram-бот с меню, профилем, пресетами, платежами (mock) и учетом токенов.

## Быстрый старт (docker-compose)

1. Скопируйте `.env.example` в `.env` и заполните:
   - `BOT_TOKEN`
   - `DATABASE_URL` (для docker-compose по умолчанию уже подходит)
   - `ADMIN_IDS` (через запятую)
   - `GEMINI_API_KEY`

2. Запуск:

```bash
docker compose up --build
```

База автоматически создаст таблицы из `db/migrations/001_init.sql`.

## Локальный запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Если база уже запущена вручную, примените миграцию:

```bash
psql "$DATABASE_URL" -f db/migrations/001_init.sql
```

## Webhook (mock подтверждения оплат)

Отдельное приложение FastAPI:

```bash
uvicorn webhook_app:app --reload --host 0.0.0.0 --port 8000
```

POST `/payments/yoomoney` или `/payments/stars` с JSON:

```json
{"order_id": "ORD-XXXX"}
```

## Структура

- `handlers/` — обработчики команд, меню, генераций, оплат
- `keyboards/` — клавиатуры
- `services/` — адаптеры API и платежей (mock)
- `db/` — модели и миграции
- `middlewares/` — middleware
- `utils/` — константы и вспомогательные функции

## Настройка пресетов

Файл `utils/presets.py` содержит список пресетов и превью. Можно заменить на свои.

## Redis FSM (опционально)

Для использования `FSM_STORAGE=redis` установите `aioredis` и задайте `REDIS_URL`.

## Заглушки

- `services/nanobanana.py` — мок генерации изображений/видео.
- `services/payments/` — мок для Card и Stars.

## Подтверждение заказов вручную

Команда администратора:

```
/confirm_order <order_id>
```
