from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram import F
from config import user_photos, user_data, log_message
from document_generator import generate_document
from aiogram.types import FSInputFile
import os

done_button = KeyboardButton(text="Готово ✅")
keyboard = ReplyKeyboardMarkup(keyboard=[[done_button]], resize_keyboard=True)

router = Router()


@router.message(F.text == "/start")
async def start_handler(message: Message):
    await message.reply(
        "Привет! Отправь мне несколько фото, и я вставлю их в отчет. Когда закончишь, нажми кнопку <b>Готово</b>.",
        parse_mode="HTML",
    )
    log_message("👤 Запрос от нового пользователя", message)


@router.message(F.photo)
async def photo_handler(message: Message):
    user_id = message.from_user.id

    if user_id not in user_photos:
        user_photos[user_id] = []

    highest_quality_photo = max(message.photo, key=lambda p: p.file_size)
    user_photos[user_id].append(highest_quality_photo.file_id)

    if len(user_photos[user_id]) == 1:
        await message.reply(
            "📸 Фото получено! Отправь ещё или нажми кнопку <b>Готово</b>, чтобы завершить.",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        log_message("📷 Пользователь отправил фото", message)


@router.message(F.text == "Готово ✅")
async def done_handler(message: Message):
    user_id = message.from_user.id

    if user_id not in user_photos or not user_photos[user_id]:
        await message.reply(
            "⚠️ Вы ещё не отправили ни одной фотографии.", parse_mode="HTML"
        )
        return

    await message.reply(
        "📅 Пожалуйста, введите дату в формате ДД.ММ.ГГГГ:", parse_mode="HTML"
    )
    log_message("🖼️ Фото от пользователя сохранены", message)

    user_data[user_id] = {"photos": user_photos[user_id]}


@router.message(F.text.regexp(r"\d{2}\.\d{2}\.\d{4}"))
async def date_handler(message: Message):
    user_id = message.from_user.id

    if user_id not in user_data:
        await message.reply(
            "⚠️ Пожалуйста, сначала нажмите 'Готово ✅'.", parse_mode="HTML"
        )
        return

    user_data[user_id]["date"] = message.text
    await message.reply("📍 Пожалуйста, введите адрес:", parse_mode="HTML")
    log_message("📅 Дата от пользователя сохранена", message)


@router.message(F.text)
async def address_handler(message: Message):
    user_id = message.from_user.id

    if user_id not in user_data or "date" not in user_data[user_id]:
        return

    user_data[user_id]["address"] = message.text
    await message.reply("📝 Создаю документ, подождите немного...", parse_mode="HTML")
    log_message(
        "📍 Адрес от пользователя сохранен, началась обработка документа", message
    )

    try:
        output_file = await generate_document(user_id, user_data[user_id])

        await message.answer_document(FSInputFile(output_file))
        log_message("📄 Готовый отчет отправлен пользователю", message)

        os.remove(output_file)
        del user_photos[user_id]
        del user_data[user_id]
    except Exception as e:
        await message.reply(f"❌ Произошла ошибка: {e}", parse_mode="HTML")
