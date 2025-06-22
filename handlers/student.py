from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database import get_db_connection
from keyboards import get_tests_keyboard, get_homeworks_keyboard, get_lectures_keyboard, get_main_keyboard
import datetime
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(F.text == "📝 Тесты")
async def show_available_tests(message: Message):
    conn = None
    try:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db_connection()
        cursor = conn.cursor()
        logger.debug(f"Поиск доступных тестов на {now}")
        query = """
        SELECT test_id, title, description, questions, start_time, end_time 
        FROM tests 
        WHERE datetime(start_time) <= datetime(?)
        AND datetime(end_time) >= datetime(?)
        """
        
        cursor.execute(query, (now, now))
        tests = cursor.fetchall()
        
        
        if not tests:
            # Для диагностики: выводим все тесты из БД
            cursor.execute("""
                SELECT test_id, title, 
                       strftime('%d.%m.%Y %H:%M', start_time) as start_time,
                       strftime('%d.%m.%Y %H:%M', end_time) as end_time 
                FROM tests
                ORDER BY start_time
            """)
            all_tests = cursor.fetchall()
            
            if all_tests:
                response = "Все тесты в системе:\n\n"
                for test in all_tests:
                    response += f"{test[0]}. {test[1]} ({test[2]} - {test[3]})\n"
                await message.answer(response)
            
            await message.answer("Сейчас нет доступных тестов. Попробуйте позже.")
            return
            
        keyboard = get_tests_keyboard(tests)
        if keyboard:
            await message.answer("Доступные тесты:", reply_markup=keyboard)
        else:
            await message.answer("Ошибка формирования списка тестов.")
            
    except Exception as e:
        logger.error(f"Ошибка при показе тестов: {e}", exc_info=True)
        await message.answer("Произошла ошибка при загрузке тестов.")
    finally:
        if conn:
            conn.close()

@router.message(F.text == "📝 Домашние задания")
async def show_homeworks(message: Message):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT hw_id, title, description FROM homework")
        homeworks = cursor.fetchall()
        
        if not homeworks:
            await message.answer("Нет активных домашних заданий.")
            return
            
        keyboard = get_homeworks_keyboard(homeworks)
        await message.answer("Домашние задания:", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка при показе ДЗ: {e}")
        await message.answer("Ошибка загрузки домашних заданий")
    finally:
        if conn:
            conn.close()

@router.message(F.text == "📚 Лекционные материалы")
async def show_lectures(message: Message):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT material_id, title, description FROM lecture_materials")
        lectures = cursor.fetchall()
        
        if not lectures:
            await message.answer("Нет доступных лекционных материалов.")
            return
            
        keyboard = get_lectures_keyboard(lectures)
        await message.answer("Лекционные материалы:", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка при показе лекций: {e}")
        await message.answer("Ошибка загрузки материалов")
    finally:
        if conn:
            conn.close()
@router.message(F.text == "📅 Календарь")
async def show_calendar(message: Message):
    today = datetime.date.today()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT title, description, event_date FROM calendar_events WHERE event_date >= ? ORDER BY event_date",
        (today,)
    )
    events = cursor.fetchall()
    conn.close()
    
    if not events:
        await message.answer("На ближайшее время событий нет.")
        return
    
    response = "📅 Предстоящие события:\n\n"
    for event in events:
        response += f"📌 {event[0]}\n"
        response += f"📅 {event[2]}\n"
        if event[1]:
            response += f"📝 {event[1]}\n"
        response += "\n"
    
    await message.answer(response)