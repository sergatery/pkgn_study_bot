from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from states import HomeworkStates
from database import get_db_connection
from keyboards import get_cancel_keyboard
import json

router = Router()

@router.callback_query(F.data.startswith("hw_"))
async def view_homework(callback: CallbackQuery, state: FSMContext):
    hw_id = int(callback.data.split("_")[1])
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT title, description FROM homework WHERE hw_id = ?", (hw_id,))
    hw = cursor.fetchone()
    
    if not hw:
        await callback.message.answer("Домашнее задание не найдено.")
        return
    
    response = f"📝 {hw[0]}\n\n"
    if hw[1]:
        response += f"{hw[1]}\n\n"
    response += "Отправьте ваше решение в виде сообщения или файла."
    
    await callback.message.answer(response)
    await state.set_state(HomeworkStates.waiting_for_homework)
    await state.update_data(hw_id=hw_id)
    
    conn.close()

@router.message(HomeworkStates.waiting_for_homework, F.text | F.document | F.photo | F.video | F.audio)
async def submit_homework(message: Message, state: FSMContext):
    data = await state.get_data()
    hw_id = data['hw_id']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get homework info for notification
    cursor.execute("SELECT title, created_by FROM homework WHERE hw_id = ?", (hw_id,))
    hw_info = cursor.fetchone()
    
    # Save submission
    if message.text:
        cursor.execute(
            "INSERT INTO homework_submissions (hw_id, user_id, message) VALUES (?, ?, ?)",
            (hw_id, message.from_user.id, message.text)
        )
    elif message.document:
        cursor.execute(
            "INSERT INTO homework_submissions (hw_id, user_id, file_id) VALUES (?, ?, ?)",
            (hw_id, message.from_user.id, message.document.file_id)
        )
    elif message.photo:
        cursor.execute(
            "INSERT INTO homework_submissions (hw_id, user_id, file_id) VALUES (?, ?, ?)",
            (hw_id, message.from_user.id, message.photo[-1].file_id)
        )
    # Similar for other file types
    
    conn.commit()
    
    # Notify teacher
    if hw_info and hw_info[1]:
        try:
            await message.bot.send_message(
                hw_info[1],
                f"Новая сдача ДЗ '{hw_info[0]}' от {message.from_user.full_name} (@{message.from_user.username})"
            )
            if message.text:
                await message.bot.send_message(hw_info[1], message.text)
            elif message.document:
                await message.bot.send_document(hw_info[1], message.document.file_id)
            elif message.photo:
                await message.bot.send_photo(hw_info[1], message.photo[-1].file_id)
            # Similar for other file types
        except Exception as e:
            print(f"Failed to notify teacher: {e}")
    
    conn.close()
    
    await message.answer("Ваше решение отправлено преподавателю!")
    await state.clear()