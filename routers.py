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

done_button = KeyboardButton(text="Готово ✅")
keyboard = ReplyKeyboardMarkup(keyboard=[[done_button]], resize_keyboard=True)

skip_button = InlineKeyboardButton(text="Пропуск", callback_data="skip")
skip_keyboard = InlineKeyboardMarkup(inline_keyboard=[[skip_button]])

checklist_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data="work_yes"),
            InlineKeyboardButton(text="❌ Нет", callback_data="work_no"),
        ],
        [
            InlineKeyboardButton(
                text="📋 Оставить стандартные значения", callback_data="work_default"
            ),
        ],
    ]
)

router = Router()


class UserForm(StatesGroup):
    waiting_for_address = State()
    classification = State()
    materials = State()
    recommendations = State()
    defects = State()
    checklist = State()


WORKS_LIST = [
    "Ежемесячный технический осмотр оборудования на предмет его работоспособности",
    "Диагностика неисправного оборудования на предмет проведения его ремонта",
    "Проверка крепления термостатов, сигнальной арматуры, дверей и облицовки",
    "Проверка надежности крепления заземления и отсутствия механических повреждений проводов",
    "Проверка работы программных устройств",
    "Проверка нагревательных элементов, соленоидных клапанов",
    "Проверка состояния электроаппаратуры, при необходимости затяжка электроконтактных соединений, замена сгоревших плавких вставок",
    "Контроль силы тока в каждой из фаз и межфазных напряжений",
    "Проверка настройки микропроцессоров",
]


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
async def done_handler(message: Message, state: FSMContext):
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
    await state.set_state(UserForm.classification)


@router.message(F.text.regexp(r"\d{2}\.\d{2}\.\d{4}"))
async def date_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if user_id not in user_data:
        await message.reply(
            "⚠️ Пожалуйста, сначала нажмите 'Готово ✅'.", parse_mode="HTML"
        )
        return

    user_data[user_id]["date"] = message.text
    await message.reply("📍 Пожалуйста, введите адрес:", parse_mode="HTML")
    log_message("📅 Дата от пользователя сохранена", message)
    await state.set_state(UserForm.waiting_for_address)


@router.message(UserForm.waiting_for_address)
async def address_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id

    user_data[user_id]["address"] = message.text
    await message.reply(
        "🏷️ Пожалуйста, введите классификацию или нажмите 'Пропуск', чтобы оставить 'Печь':",
        reply_markup=skip_keyboard,
        parse_mode="HTML",
    )
    log_message(
        "📍 Адрес от пользователя сохранен, запрашивается классификация", message
    )
    await state.set_state(UserForm.classification)


@router.message(UserForm.classification)
async def classification_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id

    user_data[user_id]["classification"] = message.text
    await message.reply(
        "🛠️ Пожалуйста, введите материалы, применяемые при ТО, или нажмите 'Пропуск':",
        reply_markup=skip_keyboard,
        parse_mode="HTML",
    )
    log_message("🏷️ Классификация от пользователя сохранена", message)
    await state.set_state(UserForm.materials)


@router.message(UserForm.materials)
async def materials_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id

    user_data[user_id]["materials"] = message.text
    await message.reply(
        "💡 Пожалуйста, введите рекомендации или нажмите 'Пропуск':",
        reply_markup=skip_keyboard,
        parse_mode="HTML",
    )
    log_message("🛠️ Материалы от пользователя сохранены", message)
    await state.set_state(UserForm.recommendations)


@router.message(UserForm.recommendations)
async def recommendations_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id

    user_data[user_id]["recommendations"] = message.text
    await message.reply(
        "🔍 Пожалуйста, введите выявленные дефекты при ТО или нажмите 'Пропуск':",
        reply_markup=skip_keyboard,
        parse_mode="HTML",
    )
    log_message("💡 Рекомендации от пользователя сохранены", message)
    await state.set_state(UserForm.defects)


@router.callback_query(F.data == "skip")
async def skip_handler(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    message = callback_query.message

    if user_id not in user_data:
        await message.answer(
            "⚠️ Произошла ошибка: данные сессии утеряны. Пожалуйста, начните заново.",
            parse_mode="HTML",
        )
        await state.clear()
        return

    current_state = await state.get_state()

    try:
        if current_state == UserForm.classification.state:
            user_data[user_id]["classification"] = "Печь"
            await message.answer(
                "🛠️ Пожалуйста, введите материалы, применяемые при ТО, или нажмите 'Пропуск':",
                reply_markup=skip_keyboard,
                parse_mode="HTML",
            )
            log_message(
                "🏷️ Классификация пропущена, запрашиваются материалы", callback_query
            )
            await state.set_state(UserForm.materials)
        elif current_state == UserForm.materials.state:
            user_data[user_id]["materials"] = ""
            await message.answer(
                "💡 Пожалуйста, введите рекомендации или нажмите 'Пропуск':",
                reply_markup=skip_keyboard,
                parse_mode="HTML",
            )
            log_message(
                "🛠️ Материалы пропущены, запрашиваются рекомендации", callback_query
            )
            await state.set_state(UserForm.recommendations)
        elif current_state == UserForm.recommendations.state:
            user_data[user_id]["recommendations"] = ""
            await message.answer(
                "🔍 Пожалуйста, введите выявленные дефекты при ТО или нажмите 'Пропуск':",
                reply_markup=skip_keyboard,
                parse_mode="HTML",
            )
            log_message(
                "💡 Рекомендации пропущены, запрашиваются дефекты", callback_query
            )
            await state.set_state(UserForm.defects)
        elif current_state == UserForm.defects.state:
            user_data[user_id]["defects"] = ""
            log_message(
                "🔍 Дефекты пропущены, начинается заполнение чек-листа", callback_query
            )

            await message.answer(
                "📋 Заполняем чек-лист о проведенных работах", parse_mode="HTML"
            )

            await state.update_data(current_work=0, completed_works=[])

            sent_message = await message.answer(
                f"❓ {WORKS_LIST[0]}",
                reply_markup=checklist_keyboard,
                parse_mode="HTML",
            )

            await state.update_data(message_id=sent_message.message_id)
            await state.set_state(UserForm.checklist)

        await callback_query.answer()
    except Exception as e:
        log_message(f"❌ Ошибка в skip_handler: {str(e)}", callback_query)
        await message.answer(f"❌ Произошла ошибка: {str(e)}", parse_mode="HTML")


@router.message(UserForm.defects)
async def defects_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data[user_id]["defects"] = message.text

    await message.reply(
        "📋 Заполняем чек-лист о проведенных работах", parse_mode="HTML"
    )

    await state.update_data(current_work=0, completed_works=[])

    sent_message = await message.answer(
        f"❓ {WORKS_LIST[0]}", reply_markup=checklist_keyboard, parse_mode="HTML"
    )

    await state.update_data(message_id=sent_message.message_id)
    await state.set_state(UserForm.checklist)
    log_message("📋 Начато заполнение чек-листа работ", message)


@router.callback_query(lambda c: c.data in ["work_yes", "work_no", "work_default"])
async def process_work_step(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    current_data = await state.get_data()

    current_work = current_data.get("current_work", 0)
    completed_works = current_data.get("completed_works", [])

    if callback_query.data == "work_default":
        completed_works = list(range(1, len(WORKS_LIST) + 1))
        await callback_query.message.edit_text(
            "📝 Создаю документ, подождите немного...", parse_mode="HTML"
        )
        user_data[user_id]["works"] = "\n".join(
            [f"{i}. {WORKS_LIST[num-1]}" for i, num in enumerate(completed_works, 1)]
        )
        await process_document(callback_query.message, user_id, callback_query)
        await callback_query.message.edit_text("✅ Готово!", parse_mode="HTML")
        await state.clear()
        await callback_query.answer()
        return

    if callback_query.data == "work_yes":
        completed_works.append(current_work + 1)

    current_work += 1

    if current_work < len(WORKS_LIST):
        next_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Да", callback_data="work_yes"),
                    InlineKeyboardButton(text="❌ Нет", callback_data="work_no"),
                ]
            ]
        )

        await callback_query.message.edit_text(
            f"❓ {WORKS_LIST[current_work]}", reply_markup=next_keyboard
        )
        await state.update_data(
            current_work=current_work, completed_works=completed_works
        )
    else:
        await callback_query.message.edit_text(
            "📝 Создаю документ, подождите немного...", parse_mode="HTML"
        )

        if completed_works:
            works_text = "\n".join(
                [
                    f"{i}. {WORKS_LIST[num-1]}"
                    for i, num in enumerate(completed_works, 1)
                ]
            )
        else:
            works_text = "Работы не проводились"

        user_data[user_id]["works"] = works_text
        await process_document(callback_query.message, user_id, callback_query)
        await callback_query.message.edit_text("✅ Готово!", parse_mode="HTML")
        await state.clear()

    await callback_query.answer()


async def process_document(message: Message, user_id: int, original_message=None):
    try:
        if user_id not in user_data:
            raise ValueError("Данные пользователя не найдены")

        log_msg = original_message if original_message else message
        await message.answer("👇 Ваш отчет", parse_mode="HTML")

        output_file = await generate_document(user_id, user_data[user_id])
        await message.answer_document(FSInputFile(output_file))
        log_message(
            "📄 Готовый отчет отправлен пользователю", original_message or message
        )

        os.remove(output_file)
        del user_photos[user_id]
        del user_data[user_id]
    except Exception as e:
        error_msg = f"❌ Произошла ошибка: {str(e)}\n"
        error_msg += f"Текущие данные: {user_data.get(user_id, 'Нет данных')}"
        await message.answer(error_msg, parse_mode="HTML")
        log_message(f"❌ Ошибка при создании документа: {str(e)}", log_msg)
