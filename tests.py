from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from states import TestStates
from database import get_db_connection
import json
import datetime
import logging
from typing import Dict, List

router = Router()
logger = logging.getLogger(__name__)

def validate_questions(questions: List[dict]):
    """Проверяет корректность структуры вопросов"""
    if not isinstance(questions, list):
        raise ValueError("Questions should be a list")
    
    for i, q in enumerate(questions):
        if not isinstance(q, dict):
            raise ValueError(f"Question {i} should be a dictionary")
        if not all(k in q for k in ['text', 'options', 'correct']):
            raise ValueError(f"Question {i} missing required fields")
        if not isinstance(q['options'], list) or len(q['options']) < 2:
            raise ValueError(f"Question {i} has invalid options")
        if not isinstance(q['correct'], int) or q['correct'] < 0 or q['correct'] >= len(q['options']):
            raise ValueError(f"Question {i} has invalid correct index")

def validate_answer(answer_text: str, options: List[str]) -> int | None:
    """Проверяет и преобразует ответ пользователя"""
    try:
        answer = int(answer_text.strip())
        if 1 <= answer <= len(options):
            return answer - 1  # Конвертируем в 0-based индекс
    except ValueError:
        return None

def format_options(options: List[str]) -> str:
    """Форматирует варианты ответов для отображения"""
    return "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(options))

def calculate_score(questions: List[dict], answers: Dict[int, int]) -> int:
    """Подсчитывает количество правильных ответов"""
    return sum(
        1 for i, q in enumerate(questions) 
        if answers.get(i) == q['correct']
    )

async def notify_teacher(message: Message, cursor, test_id: int, score: int, total: int):
    """Отправляет уведомление преподавателю"""
    try:
        cursor.execute("""
            SELECT title, created_by FROM tests WHERE test_id = ?
        """, (test_id,))
        test_info = cursor.fetchone()
        
        if test_info and test_info[1]:
            teacher_id = test_info[1]
            test_title = test_info[0]
            student_name = message.from_user.id
            percentage = score / total
            
            await message.bot.send_message(
                teacher_id,
                f"📌 Новый результат теста:\n"
                f"📝 Название: {test_title}\n"
                f"👤 Студент: {student_name}\n"
                f"📊 Результат: {score}/{total} ({percentage:.0%})"
            )
    except Exception as e:
        logger.error(f"Failed to notify teacher: {e}", exc_info=True)

def get_result_feedback(percentage: float) -> str:
    """Возвращает текстовую оценку результатов"""
    if percentage >= 0.9:
        return "Отличный результат! 🎉 Превосходная работа!"
    elif percentage >= 0.7:
        return "Хороший результат! 👍 Вы хорошо справились."
    elif percentage >= 0.5:
        return "Удовлетворительно. Есть куда расти! 📚"
    else:
        return "Неудовлетворительно. Рекомендуем повторить материал. 🧠"

@router.callback_query(F.data.startswith("test_"))
async def start_test(callback: CallbackQuery, state: FSMContext):
    conn = None
    try:
        test_id = int(callback.data.split("_")[1])
        user_id = callback.from_user.id
        
        logger.info(f"User {user_id} starts test {test_id}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, questions, start_time, end_time 
            FROM tests 
            WHERE test_id = ?
            AND datetime(start_time) <= datetime('now', 'localtime')
            AND datetime(end_time) >= datetime('now', 'localtime')
        """, (test_id,))
        test = cursor.fetchone()
        
        if not test:
            await callback.message.answer("❌ Тест недоступен. Проверьте сроки проведения.")
            return
            
        cursor.execute("""
            SELECT 1 FROM test_results 
            WHERE test_id = ? AND user_id = ? 
            LIMIT 1
        """, (test_id, user_id))
        if cursor.fetchone():
            await callback.message.answer("⚠️ Вы уже проходили этот тест.")
            return
            
        try:
            questions = json.loads(test[1])
            validate_questions(questions)
        except Exception as e:
            logger.error(f"Invalid test format: {e}")
            await callback.message.answer("❌ Ошибка в формате теста. Сообщите преподавателю.")
            return
            
        await state.set_state(TestStates.taking_test)
        await state.set_data({
            'test_id': test_id,
            'questions': questions,
            'current_question': 0,
            'answers': {},
            'start_time': datetime.datetime.now().isoformat()
        })
        
        await callback.answer()
        await send_question(callback.message, state)
        
    except Exception as e:
        logger.error(f"Error in start_test: {e}", exc_info=True)
        await callback.message.answer("❌ Ошибка при запуске теста")
    finally:
        if conn:
            conn.close()

async def send_question(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        current = data['current_question']
        questions = data['questions']
        
        if current >= len(questions):
            await submit_test(message, state)
            return
            
        question = questions[current]
        options = format_options(question['options'])
        
        await message.answer(
            f"❓ Вопрос {current+1}/{len(questions)}:\n\n"
            f"{question['text']}\n\n"
            f"Варианты:\n{options}\n\n"
            "➡️ Введите номер правильного ответа:"
        )
    except Exception as e:
        logger.error(f"Error in send_question: {e}")
        await message.answer("❌ Ошибка при загрузке вопроса")
        await state.clear()

@router.message(TestStates.taking_test, F.text)
async def process_test_answer(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        current = data['current_question']
        questions = data['questions']
        answers = data['answers']
        
        answer = validate_answer(message.text, questions[current]['options'])
        if answer is None:
            await message.answer("⚠️ Введите номер варианта (1, 2, 3...). Попробуйте снова:")
            return
            
        answers[current] = answer
        
        await state.update_data({
            'current_question': current + 1,
            'answers': answers
        })
        
        await send_question(message, state)
        
    except Exception as e:
        logger.error(f"Error in process_answer: {e}")
        await message.answer("❌ Ошибка обработки ответа")
        await state.clear()

async def submit_test(message: Message, state: FSMContext):
    conn = None
    try:
        data = await state.get_data()
        test_id = data['test_id']
        questions = data['questions']
        answers = data.get('answers', {})
        user_id = message.from_user.id
        
        score = calculate_score(questions, answers)
        percentage = score / len(questions)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO test_results 
            (test_id, user_id, answers, score, total_questions) 
            VALUES (?, ?, ?, ?, ?)
        """, (
            test_id, 
            user_id, 
            json.dumps(answers), 
            score, 
            len(questions)
        ))
        
        await notify_teacher(message, cursor, test_id, score, len(questions))
        conn.commit()
        
        await message.answer(
            f"📊 Тест завершен!\n"
            f"✅ Правильных ответов: {score} из {len(questions)}\n"
            f"📈 Результат: {percentage:.0%}\n\n"
            f"{get_result_feedback(percentage)}"
        )
    except Exception as e:
        logger.error(f"Error in submit_test: {e}", exc_info=True)
        await message.answer("❌ Ошибка при сохранении результатов")
    finally:
        if conn:
            conn.close()
        await state.clear()