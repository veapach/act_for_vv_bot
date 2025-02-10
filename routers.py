import re
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
from database import db
import os
from datetime import datetime, timedelta

router = Router()


class UserForm(StatesGroup):
    waiting_for_last_name = State()
    waiting_for_first_name = State()
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
    waiting_for_start_date = State()
    waiting_for_end_date = State()
    waiting_for_address_search = State()


new_report_button = KeyboardButton(text="📝 Новый отчет")
view_reports_button = KeyboardButton(text="📊 Просмотреть отчеты")
done_button = KeyboardButton(text="✅ Готово")
cancel_button = KeyboardButton(text="❌ Отмена")

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[[new_report_button], [view_reports_button]], resize_keyboard=True
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
async def start_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id

    user = await db.get_user(user_id)
    if user:
        first_name, last_name = user
        await message.reply(
            f"С возвращением, {first_name} {last_name}! Нажми кнопку 📝 Новый отчет, чтобы начать.",
            reply_markup=main_keyboard,
            parse_mode="HTML",
        )
        return

    await state.set_state(UserForm.waiting_for_last_name)
    await message.reply("Пожалуйста, введите вашу фамилию:")


@router.message(UserForm.waiting_for_last_name)
async def last_name_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    last_name = message.text.strip()

    if not last_name.isalpha():
        await message.reply("❌ Пожалуйста, введите корректную фамилию.")
        return

    await state.update_data(last_name=last_name)
    await state.set_state(UserForm.waiting_for_first_name)
    await message.reply("Пожалуйста, введите ваше имя:")


@router.message(UserForm.waiting_for_first_name)
async def first_name_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    first_name = message.text.strip()

    if not first_name.isalpha():
        await message.reply("❌ Пожалуйста, введите корректное имя.")
        return

    user_data_state = await state.get_data()
    last_name = user_data_state.get("last_name")

    await db.add_user(user_id, first_name=first_name, last_name=last_name)

    await log_message(
        "Новый пользователь", user=f"{first_name} {last_name} (ID: {user_id})"
    )

    await message.reply(
        f"Привет, {first_name} {last_name}! Нажми кнопку 📝 Новый отчет, чтобы начать.",
        reply_markup=main_keyboard,
        parse_mode="HTML",
    )

    await state.clear()


@router.message(F.text == "📝 Новый отчет")
async def new_report_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id

    user_record = await db.get_user(user_id)
    if not user_record:
        await message.reply(
            "❌ Вы не зарегистрированы. Пожалуйста, используйте команду /start для регистрации."
        )
        await state.set_state(UserForm.waiting_for_last_name)
        return

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
async def done_button_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id

    user_record = await db.get_user(user_id)
    if not user_record:
        await message.reply(
            "❌ Вы не зарегистрированы. Пожалуйста, используйте команду /start для регистрации."
        )
        await state.set_state(UserForm.waiting_for_last_name)
        return

    required_fields = [
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
    await process_document(message, state, user_id)


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

    user_data[user_id]["photos"] = user_photos.get(user_id, [])

    await log_message("Завершил загрузку фото", user=username)
    await delete_and_update(callback.message, user_id)
    await state.clear()
    await callback.answer()


@router.message(UserForm.waiting_for_date)
async def date_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = (
        message.from_user.username or f"{message.from_user.first_name} (ID: {user_id})"
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
    user = f"{callback.from_user.first_name} {callback.from_user.last_name} (ID: {user_id})"
    await callback.message.edit_text("📝 Создаю документ, подождите немного...")

    try:
        output_file = await process_document(callback.message, user_id, callback)

        sent_message = await callback.message.answer_document(FSInputFile(output_file))

        await log_message("Документ успешно отправлен", user=user)

        os.remove(output_file)

        await callback.message.answer(
            "✅ Отчет создан!\nНажмите 📝 Новый отчет для создания нового отчета",
            reply_markup=main_keyboard,
        )
    except Exception as e:
        error_text = f"Ошибка при создании документа: {str(e)}"
        await log_message(error_text, user=user)
        await callback.message.edit_text(
            "❌ Произошла ошибка при создании документа. Попробуйте еще раз."
        )


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


async def process_document(
    message: Message, state: FSMContext, user_id: int, original_message=None
):
    try:
        if user_id not in user_data:
            raise ValueError("Данные пользователя не найдены")

        username = (
            message.from_user.username
            or f"{message.from_user.first_name} (ID: {user_id})"
        )
        await log_message("Начал создание документа", user=username)

        user_info = user_data[user_id]
        photos = user_info.get("photos", [])

        user_record = await db.get_user(user_id)
        if not user_record:
            await message.answer(
                "❌ Вы не зарегистрированы. Пожалуйста, используйте команду /start для регистрации."
            )
            await state.set_state(UserForm.waiting_for_last_name)
            return

        output_file = await generate_document(user_id, user_info)

        sent_message = await message.answer_document(FSInputFile(output_file))

        date = user_info.get("date")
        address = user_info.get("address")
        await db.add_report(user_id, sent_message.message_id, date, address)

        await log_message("Документ успешно отправлен", user=username)

        os.remove(output_file)
        if user_id in user_photos:
            del user_photos[user_id]
        if user_id in user_data:
            del user_data[user_id]

        await message.answer(
            "✅ Отчет создан!\nНажмите 📝 Новый отчет для создания нового отчета",
            reply_markup=main_keyboard,
        )
    except ValueError as ve:
        await message.answer(str(ve))
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")


@router.message(F.text == "📊 Просмотреть отчеты")
async def view_reports_handler(message: Message):
    user = message.from_user.username or message.from_user.id
    await log_message(f"[USER: {user}] [LOG] - Начал просмотр отчетов")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="По дате", callback_data="view_by_date"),
                InlineKeyboardButton(text="По номеру", callback_data="view_by_number"),
            ]
        ]
    )
    await message.reply("Выберите способ поиска отчетов:", reply_markup=keyboard)


@router.callback_query(F.data == "view_by_date")
async def view_reports_by_date(callback: types.CallbackQuery, state: FSMContext):
    user = callback.from_user.username or callback.from_user.id
    await log_message(f"[USER: {user}] [LOG] - Выбрал просмотр отчетов по дате")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Все за вчера", callback_data="view_yesterday"
                ),
                InlineKeyboardButton(text="Все за сегодня", callback_data="view_today"),
            ]
        ]
    )
    await callback.message.edit_text(
        "Введите дату 'от' в формате ДД.ММ.ГГГГ, либо выберите ниже:",
        reply_markup=keyboard,
    )
    await state.set_state(UserForm.waiting_for_start_date)
    await callback.answer()


@router.callback_query(F.data == "view_yesterday")
async def view_reports_yesterday(callback: types.CallbackQuery):
    user = callback.from_user.username or callback.from_user.id
    await log_message(f"[USER: {user}] [LOG] - Запросил отчеты за вчера")

    user_id = callback.from_user.id
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")

    report_ids = await db.get_reports(user_id, yesterday, yesterday)
    await send_reports(callback.message, report_ids)
    await callback.answer()


@router.callback_query(F.data == "view_today")
async def view_reports_today(callback: types.CallbackQuery):
    user = callback.from_user.username or callback.from_user.id
    await log_message(f"[USER: {user}] [LOG] - Запросил отчеты за сегодня")

    user_id = callback.from_user.id
    today = datetime.now().strftime("%d.%m.%Y")

    report_ids = await db.get_reports(user_id, today, today)
    await send_reports(callback.message, report_ids)
    await callback.answer()


@router.message(UserForm.waiting_for_start_date)
async def start_date_handler(message: Message, state: FSMContext):
    user = message.from_user.username or message.from_user.id
    await log_message(f"[USER: {user}] [LOG] - Вводит начальную дату отчета")

    start_date = message.text.strip()
    if not validate_date(start_date):
        await message.reply(
            "❌ Пожалуйста, введите корректную дату 'от' в формате ДД.ММ.ГГГГ:"
        )
        return

    await state.update_data(start_date=start_date)
    await message.reply("Введите дату 'до' в формате ДД.ММ.ГГГГ:")
    await state.set_state(UserForm.waiting_for_end_date)


@router.message(UserForm.waiting_for_end_date)
async def end_date_handler(message: Message, state: FSMContext):
    user = message.from_user.username or message.from_user.id
    await log_message(f"[USER: {user}] [LOG] - Вводит конечную дату отчета")

    end_date = message.text.strip()
    user_data_state = await state.get_data()
    start_date = user_data_state.get("start_date")

    if not validate_date(end_date):
        await message.reply(
            "❌ Пожалуйста, введите корректную дату 'до' в формате ДД.ММ.ГГГГ:"
        )
        return

    report_ids = await db.get_reports(message.from_user.id, start_date, end_date)
    await send_reports(message, report_ids)
    await state.clear()


@router.callback_query(F.data == "view_by_number")
async def view_reports_by_address(callback: types.CallbackQuery, state: FSMContext):
    user = callback.from_user.username or callback.from_user.id
    await log_message(f"[USER: {user}] [LOG] - Выбрал просмотр отчетов по номеру")

    await callback.message.edit_text("Введите номер для поиска отчетов:")
    await state.set_state(UserForm.waiting_for_address_search)
    await callback.answer()


@router.message(UserForm.waiting_for_address_search)
async def number_search_handler(message: Message, state: FSMContext):
    user = message.from_user.username or message.from_user.id
    await log_message(f"[USER: {user}] [LOG] - Выполняет поиск отчетов по номеру")

    number = message.text.strip()
    user_id = message.from_user.id

    report_ids = await db.get_reports_by_number(user_id, number)
    if report_ids:
        for report_id in report_ids:
            try:
                await message.bot.forward_message(
                    chat_id=user_id,
                    from_chat_id=message.chat.id,
                    message_id=report_id[0],
                )
            except Exception as e:
                await message.reply(f"❌ Не удалось переслать отчет: {str(e)}")
    else:
        await message.reply("📄 Нет отчетов с указанным номером.")

    await state.clear()


async def send_reports(message, report_ids):
    user = message.chat.username or message.chat.id
    await log_message(f"[USER: {user}] [LOG] - Отправляет отчеты")

    user_id = message.chat.id
    if report_ids:
        for report_id in report_ids:
            try:
                await message.bot.forward_message(
                    chat_id=user_id,
                    from_chat_id=message.chat.id,
                    message_id=report_id[0],
                )
            except Exception as e:
                await message.reply(f"❌ Ошибка при пересылке отчета: {str(e)}")
    else:
        await message.reply("📄 Нет отчетов за указанный период.")


def validate_date(date_str):
    if not re.match(r"^\d{2}\.\d{2}\.\d{4}$", date_str):
        return False
    try:
        datetime.strptime(date_str, "%d.%m.%Y")
        return True
    except ValueError:
        return False


async def fetch_reports(user_id, start_date, end_date):
    reports = await db.get_reports(user_id, start_date, end_date)

    if not reports:
        return []

    report_files = []
    for report in reports:
        report_file_path = report["file_path"]
        report_files.append(report_file_path)

    return report_files
