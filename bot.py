import os
from io import BytesIO
from aiogram import Bot, Dispatcher, Router
from aiogram.types import ContentType, Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile
from aiogram import F
from aiogram.types import Message
from aiogram.client.session.aiohttp import AiohttpSession
from docx import Document
from docx.shared import Cm
from docx.oxml import parse_xml
from docx.oxml.ns import nsmap
from PIL import Image
from config import API_TOKEN
import asyncio


# Создаем клавиатуру с кнопкой "Готово ✅"
done_button = KeyboardButton(text="Готово ✅")
keyboard = ReplyKeyboardMarkup(keyboard=[[done_button]], resize_keyboard=True)

# Создаем бота и диспетчер
bot = Bot(token=API_TOKEN, session=AiohttpSession())
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# Хранилище для фотографий и данных пользователей
user_photos = {}
user_data = {}


@router.message(F.text == "/start")
async def start_handler(message: Message):
    await message.reply(
        "Привет! Отправь мне несколько фото, и я вставлю их в отчет. Когда закончишь, нажми кнопку <b>Готово</b>.",
        parse_mode="HTML",
    )
    username = message.from_user.username or "неизвестный"
    print(f"[LOG] - Запрос от нового пользователя! @{username}")


@router.message(F.photo)
async def photo_handler(message: Message):
    user_id = message.from_user.id

    if user_id not in user_photos:
        user_photos[user_id] = []

    # Сохраняем только фото с наивысшим разрешением
    highest_quality_photo = max(message.photo, key=lambda p: p.file_size)
    user_photos[user_id].append(highest_quality_photo.file_id)

    # Отправляем сообщение с кнопкой "Готово ✅" только один раз
    if len(user_photos[user_id]) == 1:
        await message.reply(
            "📸 Фото получено! Отправь ещё или нажми кнопку <b>Готово</b>, чтобы завершить.",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        username = message.from_user.username or "неизвестный"
        print(f"[LOG] - Пользователь отправил фото @{username}")


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
    username = message.from_user.username or "неизвестный"
    print(f"[LOG] - Фото от пользователя сохранены @{username}")

    # Инициализируем данные пользователя
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
    username = message.from_user.username or "неизвестный"
    print(f"[LOG] - Дата от пользователя сохранена @{username}")


@router.message(F.text)
async def address_handler(message: Message):
    user_id = message.from_user.id

    if user_id not in user_data or "date" not in user_data[user_id]:
        return

    user_data[user_id]["address"] = message.text
    await message.reply("📝 Создаю документ, подождите немного...", parse_mode="HTML")
    username = message.from_user.username or "неизвестный"
    print(
        f"[LOG] - Адрес от пользователя сохранен, началась обработка документа @{username}"
    )

    try:
        # Генерация документа Word
        output_file = await generate_document(user_id, user_data[user_id])

        # Отправка документа пользователю
        await message.answer_document(FSInputFile(output_file))
        print(f"[LOG] - Готовый отчет отправлен пользователю @{username}")

        # Очистка временных данных
        os.remove(output_file)
        del user_photos[user_id]
        del user_data[user_id]
    except Exception as e:
        await message.reply(f"❌ Произошла ошибка: {e}", parse_mode="HTML")


# Генерация документа Word
async def generate_document(user_id, user_info):
    doc = Document("template.docx")

    # Вставка даты и адреса в таблицы документа
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if "[дата]" in cell.text:
                    cell.text = cell.text.replace("[дата]", user_info["date"])
                if "[адрес]" in cell.text:
                    cell.text = cell.text.replace("[адрес]", user_info["address"])
                if "[вставка]" in cell.text:
                    cell.text = ""  # Удаляем текст [вставка]
                    for photo_id in user_info["photos"]:
                        photo = await bot.download(file=await bot.get_file(photo_id))
                        image = Image.open(BytesIO(photo.read()))

                        # Изменение размера
                        width_cm = 18
                        height_cm = 13.5
                        dpi = 96
                        width_px = int((width_cm / 2.54) * dpi)
                        height_px = int((height_cm / 2.54) * dpi)
                        image.thumbnail((width_px, height_px))

                        # Сохранение временного изображения
                        temp_image_path = f"temp_{user_id}_{photo_id}.jpg"
                        image.save(temp_image_path)

                        # Вставка изображения
                        paragraph = cell.add_paragraph()
                        paragraph.alignment = 1  # Центрирование параграфа
                        run = paragraph.add_run()
                        run.add_picture(
                            temp_image_path, width=Cm(width_cm), height=Cm(height_cm)
                        )

                        os.remove(temp_image_path)

    # Формирование имени выходного файла
    date = user_info["date"]
    address = user_info["address"]
    output_path = f"Отчет о проведенном ТО-{date}  {address}.docx"
    doc.save(output_path)
    return output_path


async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    print("[LOG] - Бот запущен успешно")
    await dp.start_polling(bot, parse_mode="HTML")


if __name__ == "__main__":
    asyncio.run(main())
