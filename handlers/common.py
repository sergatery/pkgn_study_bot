from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import get_db_connection
from keyboards import get_role_keyboard, get_main_keyboard
from config import Config

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    
    if user:
        # User exists, show main menu
        is_teacher = user[3] == 'teacher'
        await message.answer(
            f"Добро пожаловать, {'преподаватель' if is_teacher else 'студент'}!",
            reply_markup=get_main_keyboard(is_teacher)
        )
    else:
        # New user, ask for role
        await message.answer(
            "Добро пожаловать! Пожалуйста, выберите вашу роль:",
            reply_markup=get_role_keyboard()
        )
    
    conn.close()

@router.message(F.text == "👨‍🎓 Я студент")
async def set_role_student(message: Message, state: FSMContext):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Add user as student
    cursor.execute(
        "INSERT INTO users (user_id, username, full_name, role) VALUES (?, ?, ?, ?)",
        (message.from_user.id, message.from_user.username, message.from_user.full_name, 'student')
    )
    conn.commit()
    conn.close()
    
    await message.answer(
        "Вы зарегистрированы как студент!",
        reply_markup=get_main_keyboard(False)
    )

@router.message(F.text == "👨‍🏫 Я преподаватель")
async def set_role_teacher(message: Message, state: FSMContext):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user is in admin list
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("Извините, у вас нет прав преподавателя.")
        return
    
    # Add user as teacher
    cursor.execute(
        "INSERT INTO users (user_id, username, full_name, role) VALUES (?, ?, ?, ?)",
        (message.from_user.id, message.from_user.username, message.from_user.full_name, 'teacher')
    )
    conn.commit()
    conn.close()
    
    await message.answer(
        "Вы зарегистрированы как преподаватель!",
        reply_markup=get_main_keyboard(True)
    )

@router.message(F.text == "🔙 Назад")
async def back_to_main(message: Message, state: FSMContext):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT role FROM users WHERE user_id = ?", (message.from_user.id,))
    role = cursor.fetchone()[0]
    conn.close()
    
    await message.answer(
        "Главное меню",
        reply_markup=get_main_keyboard(role == 'teacher')
    )
    await state.clear()