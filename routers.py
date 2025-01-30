from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from config import user_photos, user_data, log_message
from document_generator import generate_document
from aiogram.types import FSInputFile
import os

router = Router()


class UserForm(StatesGroup):
    waiting_for_photos = State()
    waiting_for_date = State()
    waiting_for_address = State()
    waiting_for_classification = State()
    waiting_for_classification_input = State()
    waiting_for_materials = State()
    waiting_for_recommendations = State()
    waiting_for_defects = State()
    checklist = State()
    waiting_for_additional_works = State()


new_report_button = KeyboardButton(text="📝 Новый отчет")
done_button = KeyboardButton(text="✅ Готово")
cancel_button = KeyboardButton(text="❌ Отмена")

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[[new_report_button]], resize_keyboard=True
)
report_keyboard = ReplyKeyboardMarkup(
    keyboard=[[done_button, cancel_button]], resize_keyboard=True
)


async def delete_and_update(message: Message, user_id: int):
    try:
        await message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
    await update_report_message(message, user_id)


WORKS_LIST = [
    "Ежемесячный технический осмотр оборудования на предмет его работоспособности.",
    "Технический осмотр оборудования на предмет его работоспособности.",
    "Диагностика неисправного оборудования на предмет проведения его ремонта.",
    "Диагностика оборудования",
    "Проверка крепления термостатов, сигнальной арматуры, дверей и облицовки.",
    "Проверка надежности крепления заземления и отсутствия механических повреждений проводов.",
    "Проверка работы программных устройств.",
    "Проверка нагревательных элементов.",
    "Проверка соленоидных клапанов.",
    "Проверка состояния электроаппаратуры, при необходимости затяжка электроконтактных соединений, замена сгоревших плавких вставок.",
    "Контроль силы тока в каждой из фаз и межфазных напряжений.",
    "Проверка настройки микропроцессоров",
    "Контрольная проверка агрегата в рабочем режиме.",
]


def get_report_keyboard(user_id):
    data = user_data.get(user_id, {})
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{'✅' if 'photos' in data else '❌'} Фотографии",
                callback_data="upload_photos",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if 'date' in data else '❌'} Дата",
                callback_data="upload_date",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if 'address' in data else '❌'} Адрес",
                callback_data="upload_address",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if 'classification' in data else '❌'} Классификация",
                callback_data="upload_classification",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if 'materials' in data else '❌'} Материалы",
                callback_data="upload_materials",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if 'recommendations' in data else '❌'} Рекомендации",
                callback_data="upload_recommendations",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if 'defects' in data else '❌'} Дефекты",
                callback_data="upload_defects",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if 'works' in data else '❌'} Чек-лист работ",
                callback_data="upload_works",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if 'additional_works' in data else '❌'} Дополнительные работы",
                callback_data="upload_additional_works",
            )
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def update_report_message(message: Message, user_id: int):
    await message.answer(
        "📋 Создание отчета\nВыберите, что хотите заполнить:",
        reply_markup=get_report_keyboard(user_id),
        parse_mode="HTML",
    )


@router.message(F.text == "/start")
async def start_handler(message: Message):
    user_id = message.from_user.id
    username = (
        message.from_user.username or f"{message.from_user.first_name} (ID: {user_id})"
    )
    await log_message("Новый пользователь", user=username)
    await message.reply(
        "Привет! Нажми кнопку 📝 Новый отчет, чтобы начать.",
        reply_markup=main_keyboard,
        parse_mode="HTML",
    )


@router.message(F.text == "📝 Новый отчет")
async def new_report_handler(message: Message):
    user_id = message.from_user.id
    username = (
        message.from_user.username or f"{message.from_user.first_name} (ID: {user_id})"
    )
    await log_message("Начал создание нового отчета", user=username)
    user_data[user_id] = {}
    user_photos[user_id] = []
    await message.answer(
        "Создание нового отчета начато. Выберите, что хотите заполнить:",
        reply_markup=report_keyboard,
    )
    await update_report_message(message, user_id)


@router.message(F.text == "❌ Отмена")
async def cancel_report_handler(message: Message):
    user_id = message.from_user.id
    if user_id in user_data:
        del user_data[user_id]
    if user_id in user_photos:
        del user_photos[user_id]
    await message.answer("Создание отчета отменено", reply_markup=main_keyboard)


@router.message(F.text == "✅ Готово")
async def done_button_handler(message: Message):
    user_id = message.from_user.id

    required_fields = [
        "photos",
        "date",
        "address",
        "classification",
        "materials",
        "recommendations",
        "defects",
        "works",
    ]
    missing_fields = [
        field for field in required_fields if field not in user_data.get(user_id, {})
    ]

    if missing_fields:
        missing_text = ", ".join(missing_fields)
        await message.answer(f"❌ Необходимо заполнить: {missing_text}")
        return

    await message.answer("📝 Создаю документ, подождите немного...")
    await process_document(message, user_id)


@router.callback_query(F.data.startswith("upload_"))
async def upload_handler(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data.split("_", 1)[1]
    user = callback.from_user
    username = user.username or f"{user.first_name} (ID: {user.id})"
    log_text = f"Начал заполнение {action}"
    await log_message(log_text, user=username)

    if action in user_data.get(user.id, {}):
        if action == "photos":
            user_photos[user.id] = []
        else:
            user_data[user.id][action] = None

    messages_map = {
        "photos": "📸 Отправьте фотографии для отчета (можно отправить несколько). После завершения нажмите кнопку Готово",
        "date": "📅 Введите дату в формате ДД.ММ.ГГГГ",
        "address": "📍 Введите адрес",
        "classification": "🏷️ Выберите классификацию",
        "materials": "🛠️ Введите материалы или нажмите Пропуск",
        "recommendations": "💡 Введите рекомендации или нажмите Пропуск",
        "defects": "🔍 Введите выявленные дефекты или нажмите Пропуск",
        "works": "📋 Заполните чек-лист работ",
        "additional_works": "🔧 Введите дополнительные работы или нажмите Пропуск",
    }

    states_map = {
        "photos": UserForm.waiting_for_photos,
        "date": UserForm.waiting_for_date,
        "address": UserForm.waiting_for_address,
        "classification": UserForm.waiting_for_classification,
        "materials": UserForm.waiting_for_materials,
        "recommendations": UserForm.waiting_for_recommendations,
        "defects": UserForm.waiting_for_defects,
        "works": UserForm.checklist,
        "additional_works": UserForm.waiting_for_additional_works,
    }

    skip_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Пропуск", callback_data="skip")]]
    )

    if action == "works":
        await start_checklist(callback, state)
        return

    await state.set_state(states_map[action])

    reply_markup = None

    if action == "photos":
        done_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Готово", callback_data="photos_done")]
            ]
        )
        reply_markup = done_keyboard
    elif action == "classification":
        classification_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="ПНР", callback_data="classification_pnr")],
                [
                    InlineKeyboardButton(
                        text="Аварийный вызов", callback_data="classification_emergency"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="ТО", callback_data="classification_maintenance"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Другое", callback_data="classification_other"
                    )
                ],
            ]
        )
        reply_markup = classification_keyboard
    elif action in ["materials", "recommendations", "defects", "additional_works"]:
        reply_markup = skip_keyboard

    await callback.message.edit_text(
        messages_map[action], reply_markup=reply_markup, parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("classification_"))
async def handle_classification_selection(
    callback: types.CallbackQuery, state: FSMContext
):
    user_id = callback.from_user.id
    action = callback.data.split("_", 1)[1]

    if action == "other":
        await state.set_state(UserForm.waiting_for_classification_input)
        cancel_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ Отмена", callback_data="classification_cancel_input"
                    )
                ]
            ]
        )
        await callback.message.edit_text(
            "Введите свою классификацию:", reply_markup=cancel_keyboard
        )
    else:
        classification_text = {
            "pnr": "ПНР",
            "emergency": "Аварийный вызов",
            "maintenance": "ТО",
        }.get(action, action)

        user_data[user_id]["classification"] = classification_text
        await delete_and_update(callback.message, user_id)
        await state.clear()
        await callback.answer()


@router.callback_query(F.data == "classification_cancel_input")
async def handle_classification_cancel(
    callback: types.CallbackQuery, state: FSMContext
):
    await state.clear()
    classification_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ПНР", callback_data="classification_pnr")],
            [
                InlineKeyboardButton(
                    text="Аварийный вызов", callback_data="classification_emergency"
                )
            ],
            [
                InlineKeyboardButton(
                    text="ТО", callback_data="classification_maintenance"
                )
            ],
            [InlineKeyboardButton(text="Другое", callback_data="classification_other")],
        ]
    )
    await callback.message.edit_text(
        "🏷️ Выберите классификацию:", reply_markup=classification_keyboard
    )
    await callback.answer()


@router.message(UserForm.waiting_for_classification_input)
async def handle_custom_classification_input(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data[user_id]["classification"] = message.text
    await delete_and_update(message, user_id)
    await state.clear()


@router.message(UserForm.waiting_for_photos)
async def photo_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = (
        message.from_user.username
        or f"{message.from_user.first_name} (ID: {message.from_user.id})"
    )

    if not message.photo and not message.document:
        await message.reply("❌ Пожалуйста, отправьте фотографию")
        return

    if user_id not in user_photos:
        user_photos[user_id] = []

    file_id = None
    if message.photo:
        highest_quality_photo = max(message.photo, key=lambda p: p.file_size)
        file_id = highest_quality_photo.file_id
    elif message.document and message.document.mime_type.startswith("image/"):
        file_id = message.document.file_id
    else:
        await message.reply("❌ Пожалуйста, отправьте изображение")
        return

    user_photos[user_id].append(file_id)
    user_data[user_id]["photos"] = user_photos[user_id]

    media_group_id = message.media_group_id
    if not media_group_id or len(user_photos[user_id]) == 1:
        done_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Готово", callback_data="photos_done")]
            ]
        )
        await message.reply(
            "📸 Фото добавлено! Отправьте еще или нажмите Готово",
            reply_markup=done_keyboard,
        )

    await log_message(f"Добавил фото", user=username)


@router.callback_query(F.data == "photos_done")
async def photos_done_handler(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    username = (
        callback.from_user.username
        or f"{callback.from_user.first_name} (ID: {callback.from_user.id})"
    )

    if not user_photos.get(user_id):
        await callback.message.edit_text("❌ Необходимо добавить хотя бы одно фото")
        return

    await log_message("Завершил загрузку фото", user=username)
    await update_report_message(callback.message, user_id)
    await state.clear()
    await callback.answer()


@router.message(UserForm.waiting_for_date)
async def date_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = (
        message.from_user.username
        or f"{message.from_user.first_name} (ID: {message.from_user.id})"
    )

    import re

    if not re.match(r"^\d{2}\.\d{2}\.\d{4}$", message.text):
        await message.reply("❌ Пожалуйста, введите дату в формате ДД.ММ.ГГГГ")
        return

    try:
        from datetime import datetime

        datetime.strptime(message.text, "%d.%m.%Y")
    except ValueError:
        await message.reply("❌ Пожалуйста, введите корректную дату")
        return

    user_data[user_id]["date"] = message.text
    await log_message(f"Добавил дату: {message.text}", user=username)
    await update_report_message(message, user_id)
    await state.clear()


@router.message(UserForm.waiting_for_address)
async def address_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data[user_id]["address"] = message.text
    await update_report_message(message, user_id)
    await state.clear()


@router.message(UserForm.waiting_for_materials)
async def materials_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data[user_id]["materials"] = message.text
    await delete_and_update(message, user_id)
    await state.clear()


@router.message(UserForm.waiting_for_recommendations)
async def recommendations_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data[user_id]["recommendations"] = message.text
    await delete_and_update(message, user_id)
    await state.clear()


@router.message(UserForm.waiting_for_defects)
async def defects_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data[user_id]["defects"] = message.text
    await delete_and_update(message, user_id)
    await state.clear()


@router.callback_query(F.data == "skip")
async def skip_handler(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    current_state = await state.get_state()

    default_values = {
        "UserForm:waiting_for_classification": "",
        "UserForm:waiting_for_materials": "",
        "UserForm:waiting_for_recommendations": "",
        "UserForm:waiting_for_defects": "",
        "UserForm:waiting_for_additional_works": "",
    }

    if current_state in default_values:
        field_name = current_state.split(":")[1].replace("waiting_for_", "")
        user_data[user_id][field_name] = default_values[current_state]
        await delete_and_update(callback.message, user_id)
        await state.clear()

    await callback.answer()


@router.callback_query(F.data == "upload_works")
async def start_checklist(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    username = (
        callback.from_user.username
        or f"{callback.from_user.first_name} (ID: {user_id})"
    )
    log_text = "Начал заполнение чек-листа"
    await log_message(log_text, user=username)
    await state.update_data(current_work=0, completed_works=[])
    checklist_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data="work_yes"),
                InlineKeyboardButton(text="❌ Нет", callback_data="work_no"),
            ],
            [
                InlineKeyboardButton(
                    text="📋 Стандартные значения", callback_data="work_default"
                ),
            ],
        ]
    )
    try:
        await callback.message.edit_text(
            f"❓ {WORKS_LIST[0]}", reply_markup=checklist_keyboard
        )
        await state.set_state(UserForm.checklist)
    except Exception as e:
        error_text = f"Ошибка при запуске чек-листа: {str(e)}"
        await log_message(error_text, user=username)
        await callback.message.edit_text(
            "Произошла ошибка при запуске чек-листа. Попробуйте еще раз."
        )


@router.callback_query(F.data == "generate_report")
async def generate_report_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.edit_text("📝 Создаю документ, подождите немного...")
    await process_document(callback.message, user_id, callback)


@router.callback_query(F.data.startswith("work_"))
async def process_work(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    action = callback.data.split("_")[1]
    data = await state.get_data()
    current_work = data.get("current_work", 0)
    completed_works = data.get("completed_works", [])

    if action == "yes":
        completed_works.append(WORKS_LIST[current_work])
    elif action == "default":
        completed_works.extend(WORKS_LIST[current_work:])
        current_work = len(WORKS_LIST) - 1
    elif action == "no":
        pass

    current_work += 1
    await state.update_data(current_work=current_work, completed_works=completed_works)

    if current_work < len(WORKS_LIST):
        checklist_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Да", callback_data="work_yes"),
                    InlineKeyboardButton(text="❌ Нет", callback_data="work_no"),
                ],
                [
                    InlineKeyboardButton(
                        text="📋 Стандартные значения", callback_data="work_default"
                    ),
                ],
            ]
        )
        await callback.message.edit_text(
            f"❓ {WORKS_LIST[current_work]}", reply_markup=checklist_keyboard
        )
    else:
        user_data[user_id]["works"] = completed_works
        await delete_and_update(callback.message, user_id)
        await state.clear()

    await callback.answer()


@router.callback_query(F.data == "finish_report")
async def finish_report_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = (
        callback.from_user.username
        or f"{callback.from_user.first_name} (ID: {callback.from_user.id})"
    )

    required_fields = [
        "photos",
        "date",
        "address",
        "classification",
        "materials",
        "recommendations",
        "defects",
        "works",
    ]
    missing_fields = [
        field for field in required_fields if field not in user_data.get(user_id, {})
    ]

    if missing_fields:
        missing_text = ", ".join(missing_fields)
        await callback.answer(
            f"❌ Необходимо заполнить: {missing_text}", show_alert=True
        )
        return

    await log_message("Начал создание документа", user=username)
    await callback.message.edit_text("📝 Создаю документ, подождите немного...")

    try:
        await process_document(callback.message, user_id, callback)
        await log_message("Документ успешно создан", user=username)
    except Exception as e:
        error_text = f"Ошибка при создании документа: {str(e)}"
        await log_message(error_text, user=username)
        await callback.message.edit_text(
            "❌ Произошла ошибка при создании документа. Попробуйте еще раз."
        )


@router.message(UserForm.waiting_for_additional_works)
async def additional_works_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data[user_id]["additional_works"] = message.text
    await delete_and_update(message, user_id)
    await state.clear()


async def process_document(message: Message, user_id: int, original_message=None):
    try:
        if user_id not in user_data:
            raise ValueError("Данные пользователя не найдены")

        username = (
            message.from_user.username
            or f"{message.from_user.first_name} (ID: {user_id})"
        )
        await log_message("Начал создание документа", user=username)

        output_file = await generate_document(user_id, user_data[user_id])
        await message.answer_document(FSInputFile(output_file))

        await log_message("Документ успешно отправлен", user=username)

        os.remove(output_file)
        del user_photos[user_id]
        del user_data[user_id]

        await message.answer(
            "✅ Отчет создан!\nНажмите 📝 Новый отчет для создания нового отчета",
            reply_markup=main_keyboard,
        )
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
