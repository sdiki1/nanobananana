import asyncio
from io import BytesIO
from typing import Optional

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ContentType
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.repositories import (
    adjust_balances,
    create_generation,
    create_transaction,
    get_user_by_tg_id,
    update_generation_status,
)
from services.nanobanana import NanoBananaClient
from utils.constants import (
    ANIMATE_WARNINGS,
    BTN_ANIMATE,
    BTN_BACK,
    BTN_BUY_TOKENS,
    BTN_MODEL_TEMPLATE,
    BTN_PRESETS,
    MAIN_MENU_BUTTONS,
    PROFILE_MENU_BUTTONS,
)
from utils.states import GenerationStates
from utils.tokens import select_token_cost


nanobanana_client = NanoBananaClient()


def _is_menu_text(text: str) -> bool:
    if text.startswith(BTN_MODEL_TEMPLATE.split("{", 1)[0]):
        return True
    if text in MAIN_MENU_BUTTONS or text in PROFILE_MENU_BUTTONS:
        return True
    if text in {BTN_BACK, BTN_BUY_TOKENS}:
        return True
    return False


async def _start_progress_message(
    message: types.Message,
    prefix: str,
    total_seconds: int = 40,
    step_seconds: int = 5,
):
    try:
        progress_message = await message.answer(f"{prefix}... ~{total_seconds} сек осталось")
    except Exception:
        return None, None, None

    stop_event = asyncio.Event()

    async def _updater():
        remaining = total_seconds
        while remaining > 0:
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=step_seconds)
                break
            except asyncio.TimeoutError:
                remaining = max(0, remaining - step_seconds)
                next_text = (
                    f"{prefix}... ~{remaining} сек осталось" if remaining > 0 else f"{prefix} почти готово..."
                )
                try:
                    await progress_message.edit_text(next_text)
                except Exception:
                    pass

    task = asyncio.create_task(_updater())
    return progress_message, stop_event, task


async def _finish_progress_message(progress_message, stop_event, task, final_text: str) -> None:
    if stop_event:
        stop_event.set()
    if task:
        try:
            await task
        except asyncio.CancelledError:
            pass
    if progress_message:
        try:
            await progress_message.edit_text(final_text)
        except Exception:
            pass


def _estimate_processing_time(model: Optional[str]) -> int:
    if model == "pro":
        return 45
    return 30


async def handle_text_prompt(message: types.Message, session: AsyncSession) -> None:
    if not message.text or message.text.startswith("/") or _is_menu_text(message.text):
        return
    user = await get_user_by_tg_id(session, message.from_user.id)
    if not user:
        await message.answer("Сначала отправьте /start")
        return

    model = user.selected_model
    cost = select_token_cost(user, model)
    if not cost:
        await message.answer("Недостаточно генераций. Пополните баланс.")
        return

    cost_diamonds, cost_bananas = cost
    user.diamonds -= cost_diamonds
    user.bananas -= cost_bananas
    await session.commit()

    await create_transaction(
        session,
        user_id=user.id,
        tx_type="spend",
        method=model,
        status="paid",
        amount_diamonds=cost_diamonds,
        amount_bananas=cost_bananas,
        payload={"prompt": message.text},
    )

    generation = await create_generation(
        session,
        user_id=user.id,
        kind="text2img",
        model=model,
        prompt=message.text,
        preset=None,
        cost_diamonds=cost_diamonds,
        cost_bananas=cost_bananas,
    )

    progress_message = None
    stop_event = None
    progress_task = None

    try:
        progress_message, stop_event, progress_task = await _start_progress_message(
            message,
            prefix="Генерирую изображение",
            total_seconds=_estimate_processing_time(model),
        )
        image_bytes = await nanobanana_client.generate_text2img(message.text, model)
        input_file = types.InputFile(BytesIO(image_bytes), filename="nanobanana.png")
        sent = await message.answer_photo(input_file, caption="Готово ✅")
        result_file_id = sent.photo[-1].file_id if sent.photo else None
        await update_generation_status(session, generation.id, "completed", result_url=result_file_id)
        await _finish_progress_message(progress_message, stop_event, progress_task, "Изображение готово ✅")
    except Exception as exc:  # noqa: BLE001
        await _finish_progress_message(
            progress_message,
            stop_event,
            progress_task,
            f"Не удалось создать изображение: {exc}",
        )
        await update_generation_status(session, generation.id, "failed", error=str(exc))
        await adjust_balances(session, user.id, diamonds_delta=cost_diamonds, bananas_delta=cost_bananas)
        await message.answer(f"❌ Не удалось создать изображение. Причина: {exc}")


async def _start_animate(
    user_id: int,
    reply_to: types.Message,
    state: FSMContext,
    session: AsyncSession,
    *,
    edit_message: bool = False,
) -> None:
    user = await get_user_by_tg_id(session, user_id)
    if not user:
        if edit_message:
            await reply_to.edit_text("Сначала отправьте /start")
        else:
            await reply_to.answer("Сначала отправьте /start")
        return
    if user.diamonds < settings.animate_cost:
        if edit_message:
            await reply_to.edit_text("Недостаточно кристаллов для оживления! Пополните баланс.")
        else:
            await reply_to.answer("Недостаточно кристаллов для оживления! Пополните баланс.")
        return
    await state.set_state(GenerationStates.waiting_photo_animate.state)
    if edit_message:
        await reply_to.edit_text("Отправьте фото для оживления 📎")
    else:
        await reply_to.answer("Отправьте фото для оживления 📎")


async def start_animate(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    await _start_animate(message.from_user.id, message, state, session)


async def start_animate_callback(
    query: types.CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    await _start_animate(query.from_user.id, query.message, state, session, edit_message=True)


async def process_animate_photo(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    user = await get_user_by_tg_id(session, message.from_user.id)
    if not user:
        await message.answer("Сначала отправьте /start")
        await state.finish()
        return
    if user.diamonds < settings.animate_cost:
        await message.answer("Недостаточно кристаллов для оживления! Пополните баланс.")
        await state.finish()
        return

    user.diamonds -= settings.animate_cost
    await session.commit()

    await create_transaction(
        session,
        user_id=user.id,
        tx_type="spend",
        method="animate",
        status="paid",
        amount_diamonds=settings.animate_cost,
        payload={"file_id": message.photo[-1].file_id},
    )

    generation = await create_generation(
        session,
        user_id=user.id,
        kind="animate",
        model=None,
        prompt=None,
        preset=None,
        cost_diamonds=settings.animate_cost,
        cost_bananas=0,
    )

    warnings_text = "\n".join(ANIMATE_WARNINGS)
    await message.answer(f"Процесс обработки запущен ✅\n\n{warnings_text}")

    progress_message = None
    stop_event = None
    progress_task = None
    progress_message, stop_event, progress_task = await _start_progress_message(
        message,
        prefix="Оживляю фото",
        total_seconds=_estimate_processing_time(None),
    )

    try:
        video_bytes = await nanobanana_client.animate_photo(message.bot, message.photo[-1].file_id)
        input_file = types.InputFile(BytesIO(video_bytes), filename="nanobanana.mp4")
        sent = await message.answer_video(input_file, caption="Видео готово ✅")
        result_file_id = sent.video.file_id if sent.video else None
        await update_generation_status(session, generation.id, "completed", result_url=result_file_id)
        await _finish_progress_message(progress_message, stop_event, progress_task, "Видео готово ✅")
    except Exception as exc:  # noqa: BLE001
        await _finish_progress_message(
            progress_message,
            stop_event,
            progress_task,
            f"Не удалось создать видео: {exc}",
        )
        await update_generation_status(session, generation.id, "failed", error=str(exc))
        await adjust_balances(session, user.id, diamonds_delta=settings.animate_cost)
        await message.answer(
            f"❌ Не удалось создать видео.\nПричина: {exc}\n💎 Кристаллы возвращены."
        )
    finally:
        await state.finish()


async def process_preset_photo(
    message: types.Message,
    session: AsyncSession,
    state: Optional[FSMContext] = None,
) -> None:
    user = await get_user_by_tg_id(session, message.from_user.id)
    if not user or not user.selected_preset:
        await message.answer(f"Выберите пресет через \"{BTN_PRESETS}\".")
        if state:
            await state.finish()
        return

    model = user.selected_model
    cost = select_token_cost(user, model)
    if not cost:
        await message.answer("Недостаточно генераций. Пополните баланс.")
        if state:
            await state.finish()
        return

    cost_diamonds, cost_bananas = cost
    user.diamonds -= cost_diamonds
    user.bananas -= cost_bananas
    await session.commit()

    await create_transaction(
        session,
        user_id=user.id,
        tx_type="spend",
        method=f"preset_{model}",
        status="paid",
        amount_diamonds=cost_diamonds,
        amount_bananas=cost_bananas,
        payload={"preset": user.selected_preset},
    )

    generation = await create_generation(
        session,
        user_id=user.id,
        kind="preset_img2img",
        model=model,
        prompt=None,
        preset=user.selected_preset,
        cost_diamonds=cost_diamonds,
        cost_bananas=cost_bananas,
    )

    progress_message = None
    stop_event = None
    progress_task = None

    try:
        progress_message, stop_event, progress_task = await _start_progress_message(
            message,
            prefix="Обрабатываю фото",
            total_seconds=_estimate_processing_time(model),
        )
        image_bytes = await nanobanana_client.generate_img2img(
            message.bot,
            message.photo[-1].file_id,
            user.selected_preset,
            model,
        )
        input_file = types.InputFile(BytesIO(image_bytes), filename="nanobanana.png")
        sent = await message.answer_photo(input_file, caption="Готово ✅")
        result_file_id = sent.photo[-1].file_id if sent.photo else None
        await update_generation_status(session, generation.id, "completed", result_url=result_file_id)
        await _finish_progress_message(progress_message, stop_event, progress_task, "Фото готово ✅")
    except Exception as exc:  # noqa: BLE001
        await _finish_progress_message(
            progress_message,
            stop_event,
            progress_task,
            f"Не удалось обработать фото: {exc}",
        )
        await update_generation_status(session, generation.id, "failed", error=str(exc))
        await adjust_balances(session, user.id, diamonds_delta=cost_diamonds, bananas_delta=cost_bananas)
        await message.answer(f"❌ Не удалось создать изображение. Причина: {exc}")
    finally:
        if state:
            await state.finish()


async def process_generic_photo(message: types.Message, session: AsyncSession) -> None:
    user = await get_user_by_tg_id(session, message.from_user.id)
    if user and user.selected_preset:
        await process_preset_photo(message, session=session)
        return
    await message.answer(f"Выберите \"{BTN_ANIMATE}\" или \"{BTN_PRESETS}\" для фото.")


def register(dp):
    dp.register_message_handler(start_animate, Text(equals=BTN_ANIMATE))
    dp.register_message_handler(handle_text_prompt, content_types=ContentType.TEXT)
    dp.register_message_handler(process_animate_photo, content_types=ContentType.PHOTO, state=GenerationStates.waiting_photo_animate)
    dp.register_message_handler(process_preset_photo, content_types=ContentType.PHOTO, state=GenerationStates.waiting_photo_preset)
    dp.register_message_handler(process_generic_photo, content_types=ContentType.PHOTO)
