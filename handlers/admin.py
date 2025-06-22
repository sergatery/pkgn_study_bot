import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from states import AdminStates
from database import get_db_connection
from keyboards import (
    get_admin_keyboard, 
    get_cancel_keyboard, 
    get_yes_no_keyboard, 
    get_back_keyboard
)
import json

router = Router()
logger = logging.getLogger(__name__)

async def parse_datetime(message: Message, text: str) -> datetime | None:
    """Парсит дату из строки с обработкой ошибок"""
    try:
        return datetime.strptime(text, "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ ЧЧ:ММ\n"
            "Пример: 31.12.2023 14:30",
            reply_markup=get_cancel_keyboard()
        )
        return None

def validate_questions(questions: list) -> bool:
    """Проверяет корректность структуры вопросов"""
    if not isinstance(questions, list):
        return False
        
    for q in questions:
        if not isinstance(q, dict):
            return False
        if not all(k in q for k in ['text', 'options', 'correct']):
            return False
        if not isinstance(q['options'], list) or len(q['options']) < 2:
            return False
        if not isinstance(q['correct'], int) or q['correct'] < 0 or q['correct'] >= len(q['options']):
            return False
            
    return True

# ===== ОБРАБОТКА ОТМЕНЫ ДЛЯ ВСЕХ РАЗДЕЛОВ =====
@router.message(
    StateFilter(
        # Тесты
        AdminStates.waiting_for_test_title,
        AdminStates.waiting_for_test_description,
        AdminStates.waiting_for_question_text,
        AdminStates.waiting_for_question_options,
        AdminStates.waiting_for_question_correct,
        AdminStates.waiting_for_more_questions,
        AdminStates.waiting_for_test_start_time,
        AdminStates.waiting_for_test_end_time,
        # ДЗ
        AdminStates.waiting_for_hw_title,
        AdminStates.waiting_for_hw_description,
        # Лекции
        AdminStates.waiting_for_lecture_title,
        AdminStates.waiting_for_lecture_description,
        AdminStates.waiting_for_lecture_content,
        # Календарь
        AdminStates.waiting_for_event_title,
        AdminStates.waiting_for_event_description,
        AdminStates.waiting_for_event_date
    ),
    F.text == "❌ Отмена"
)
async def cancel_creation(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Действие отменено",
        reply_markup=get_admin_keyboard()
    )

@router.message(F.text == "🛠 Администрирование")
async def admin_panel(message: Message, state: FSMContext):
    await message.answer(
        "Панель администратора",
        reply_markup=get_admin_keyboard()
    )

# ===== ТЕСТЫ =====
@router.message(F.text == "📝 Создать тест")
async def create_test_start(message: Message, state: FSMContext):
    await message.answer(
        "Введите название теста:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_test_title)
    await state.update_data(questions=[])

@router.message(AdminStates.waiting_for_test_title)
async def process_test_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(
        "Введите описание теста:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_test_description)

@router.message(AdminStates.waiting_for_test_description)
async def process_test_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(
        "Введите текст первого вопроса:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_question_text)

@router.message(AdminStates.waiting_for_question_text)
async def process_question_text(message: Message, state: FSMContext):
    await state.update_data(current_question={"text": message.text})
    await message.answer(
        "Введите варианты ответов через запятую:\nПример: Вариант 1, Вариант 2, Вариант 3",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_question_options)

@router.message(AdminStates.waiting_for_question_options)
async def process_question_options(message: Message, state: FSMContext):
    options = [opt.strip() for opt in message.text.split(",") if opt.strip()]
    if len(options) < 2:
        await message.answer("❌ Нужно минимум 2 варианта. Введите снова:")
        return
    
    data = await state.get_data()
    current_question = data.get("current_question", {})
    current_question["options"] = options
    await state.update_data(current_question=current_question)
    
    options_text = "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(options))
    await message.answer(
        f"Варианты:\n{options_text}\n\nВведите номер правильного ответа (1, 2, 3...):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_question_correct)

@router.message(AdminStates.waiting_for_question_correct)
async def process_question_correct(message: Message, state: FSMContext):
    try:
        correct = int(message.text) - 1
        data = await state.get_data()
        current_question = data.get("current_question", {})
        options = current_question.get("options", [])
        
        if correct < 0 or correct >= len(options):
            raise ValueError
        
        question = {
            "text": current_question["text"],
            "options": options,
            "correct": correct
        }
        
        questions = data.get("questions", [])
        questions.append(question)
        await state.update_data(questions=questions, current_question=None)
        
        await message.answer(
            "✅ Вопрос добавлен! Добавить еще вопрос?",
            reply_markup=get_yes_no_keyboard()
        )
        await state.set_state(AdminStates.waiting_for_more_questions)
    except ValueError:
        await message.answer("❌ Неверный номер. Введите корректный номер варианта:")

@router.message(AdminStates.waiting_for_more_questions, F.text == "✅ Да")
async def add_more_questions(message: Message, state: FSMContext):
    await message.answer(
        "Введите текст следующего вопроса:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_question_text)

@router.message(AdminStates.waiting_for_more_questions, F.text == "❌ Нет")
async def finish_questions(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data.get('questions'):
        await message.answer("❌ Нужно добавить хотя бы один вопрос!", reply_markup=get_cancel_keyboard())
        return
        
    await message.answer(
        "Введите дату и время начала теста (ДД.ММ.ГГГГ ЧЧ:ММ):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_test_start_time)

@router.message(AdminStates.waiting_for_test_start_time)
async def process_test_start_time(message: Message, state: FSMContext):
    start_time = await parse_datetime(message, message.text)
    if not start_time:
        return
        
    if start_time < datetime.now():
        await message.answer("❌ Дата начала не может быть в прошлом! Введите снова:")
        return
        
    await state.update_data(start_time=start_time)
    await message.answer(
        "Введите дату и время окончания теста (ДД.ММ.ГГГГ ЧЧ:ММ):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_test_end_time)

@router.message(AdminStates.waiting_for_test_end_time)
async def process_test_end_time(message: Message, state: FSMContext):
    end_time = await parse_datetime(message, message.text)
    if not end_time:
        return
        
    data = await state.get_data()
    start_time = data.get('start_time')
    
    if end_time <= start_time:
        await message.answer("❌ Дата окончания должна быть позже начала! Введите снова:")
        return
        
    await save_test_to_db(message, state, start_time, end_time)

async def save_test_to_db(message: Message, state: FSMContext, start_time: datetime, end_time: datetime):
    conn = None
    try:
        data = await state.get_data()
        questions = data.get('questions', [])
        
        if not validate_questions(questions):
            await message.answer("❌ Ошибка в вопросах теста! Начните заново.")
            await state.clear()
            return
            
        questions_json = json.dumps(questions, ensure_ascii=False)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO tests 
            (title, description, questions, start_time, end_time, created_by) 
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                data['title'],
                data['description'],
                questions_json,
                start_time.strftime("%Y-%m-%d %H:%M:%S"),
                end_time.strftime("%Y-%m-%d %H:%M:%S"),
                message.from_user.id
            )
        )
        conn.commit()
        
        await message.answer(
            f"✅ Тест создан!\n\n"
            f"📝 Название: {data['title']}\n"
            f"📅 Начало: {start_time.strftime('%d.%m.%Y %H:%M')}\n"
            f"⏰ Окончание: {end_time.strftime('%d.%m.%Y %H:%M')}\n"
            f"❓ Вопросов: {len(questions)}",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка сохранения теста: {e}", exc_info=True)
        await message.answer(
            "❌ Ошибка при сохранении теста",
            reply_markup=get_admin_keyboard()
        )
    finally:
        if conn:
            conn.close()
        await state.clear()

# ===== ДОМАШНИЕ ЗАДАНИЯ =====
@router.message(F.text == "📝 Добавить ДЗ")
async def add_homework_start(message: Message, state: FSMContext):
    await message.answer(
        "Введите название домашнего задания:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_hw_title)

@router.message(AdminStates.waiting_for_hw_title)
async def process_hw_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(
        "Введите описание задания (можно прикрепить файлы):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_hw_description)

@router.message(AdminStates.waiting_for_hw_description, F.content_type.in_({ContentType.TEXT, ContentType.DOCUMENT, ContentType.PHOTO}))
async def process_hw_description(message: Message, state: FSMContext):
    data = await state.get_data()
    
    description = message.text if message.text else ""
    file_id = None
    file_type = None
    
    if message.document:
        file_id = message.document.file_id
        file_type = "document"
    elif message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO homework (title, description, created_by) VALUES (?, ?, ?)",
            (data['title'], description, message.from_user.id)
        )
        
        if file_id:
            hw_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO homework_submissions (hw_id, user_id, file_id) VALUES (?, ?, ?)",
                (hw_id, message.from_user.id, file_id)
            )
        
        conn.commit()
        await message.answer(
            f"Домашнее задание '{data['title']}' успешно добавлено!",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при добавлении ДЗ: {e}", exc_info=True)
        await message.answer(
            "❌ Ошибка при добавлении ДЗ",
            reply_markup=get_admin_keyboard()
        )
    finally:
        conn.close()
        await state.clear()

# ===== ЛЕКЦИИ =====
@router.message(F.text == "📚 Добавить лекцию")
async def add_lecture_start(message: Message, state: FSMContext):
    await message.answer(
        "Введите название лекционного материала:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_lecture_title)

@router.message(AdminStates.waiting_for_lecture_title)
async def process_lecture_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(
        "Введите описание материала:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_lecture_description)

@router.message(AdminStates.waiting_for_lecture_description)
async def process_lecture_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(
        "Теперь можно добавить содержимое лекции (текст или файлы). "
        "Отправьте 'Готово', когда закончите.",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_lecture_content)

@router.message(AdminStates.waiting_for_lecture_content, F.text == "Готово")
async def finish_lecture_creation(message: Message, state: FSMContext):
    data = await state.get_data()
    
    if 'lecture_content' not in data or len(data['lecture_content']) == 0:
        await message.answer("Вы не добавили ни одного элемента в лекцию. Добавьте содержимое или отмените.")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO lecture_materials (title, description, created_by) VALUES (?, ?, ?)",
            (data['title'], data['description'], message.from_user.id)
        )
        material_id = cursor.lastrowid
        
        for order_num, content in enumerate(data['lecture_content'], 1):
            if content['type'] == 'text':
                cursor.execute(
                    "INSERT INTO lecture_content (material_id, message, order_num) VALUES (?, ?, ?)",
                    (material_id, content['content'], order_num)
                )
            else:
                cursor.execute(
                    "INSERT INTO lecture_content (material_id, file_id, file_type, order_num) VALUES (?, ?, ?, ?)",
                    (material_id, content['content'], content['type'], order_num)
                )
        
        conn.commit()
        await message.answer(
            f"Лекционный материал '{data['title']}' успешно создан!",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при создании лекции: {e}", exc_info=True)
        await message.answer(
            "❌ Ошибка при создании лекции",
            reply_markup=get_admin_keyboard()
        )
    finally:
        conn.close()
        await state.clear()

@router.message(AdminStates.waiting_for_lecture_content, F.content_type == ContentType.TEXT)
async def add_text_to_lecture(message: Message, state: FSMContext):
    data = await state.get_data()
    content = {'type': 'text', 'content': message.text}
    
    if 'lecture_content' not in data:
        await state.update_data(lecture_content=[content])
    else:
        lecture_content = data['lecture_content']
        lecture_content.append(content)
        await state.update_data(lecture_content=lecture_content)
    
    await message.answer(
        "Текст добавлен в лекцию. Продолжайте добавлять содержимое или отправьте 'Готово'.",
        reply_markup=get_back_keyboard()
    )

@router.message(AdminStates.waiting_for_lecture_content, F.content_type.in_({ContentType.DOCUMENT, ContentType.PHOTO, ContentType.VIDEO, ContentType.AUDIO}))
async def add_file_to_lecture(message: Message, state: FSMContext):
    data = await state.get_data()
    content = {}
    
    if message.document:
        content = {'type': 'document', 'content': message.document.file_id}
    elif message.photo:
        content = {'type': 'photo', 'content': message.photo[-1].file_id}
    elif message.video:
        content = {'type': 'video', 'content': message.video.file_id}
    elif message.audio:
        content = {'type': 'audio', 'content': message.audio.file_id}
    
    if 'lecture_content' not in data:
        await state.update_data(lecture_content=[content])
    else:
        lecture_content = data['lecture_content']
        lecture_content.append(content)
        await state.update_data(lecture_content=lecture_content)
    
    await message.answer(
        "Файл добавлен в лекцию. Продолжайте добавлять содержимое или отправьте 'Готово'.",
        reply_markup=get_back_keyboard()
    )

# ===== КАЛЕНДАРЬ =====
@router.message(F.text == "📅 Добавить событие")
async def add_event_start(message: Message, state: FSMContext):
    await message.answer(
        "Введите название события:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_event_title)

@router.message(AdminStates.waiting_for_event_title)
async def process_event_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(
        "Введите описание события:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_event_description)

@router.message(AdminStates.waiting_for_event_description)
async def process_event_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(
        "Введите дату события в формате ДД.ММ.ГГГГ:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_event_date)

@router.message(AdminStates.waiting_for_event_date)
async def process_event_date(message: Message, state: FSMContext):
    try:
        event_date = datetime.strptime(message.text, "%d.%m.%Y").date()
    except ValueError:
        await message.answer("❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ\nПример: 31.12.2023")
        return
    
    data = await state.get_data()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO calendar_events (title, description, event_date, created_by) VALUES (?, ?, ?, ?)",
            (data['title'], data['description'], event_date, message.from_user.id)
        )
        conn.commit()
        await message.answer(
            f"✅ Событие '{data['title']}' добавлено на {event_date.strftime('%d.%m.%Y')}!",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при добавлении события: {e}", exc_info=True)
        await message.answer(
            "❌ Ошибка при добавлении события",
            reply_markup=get_admin_keyboard()
        )
    finally:
        conn.close()
        await state.clear()