from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import logging

def get_role_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👨‍🎓 Я студент")],
            [KeyboardButton(text="👨‍🏫 Я преподаватель")]
        ],
        resize_keyboard=True
    )

def get_main_keyboard(is_teacher=False):
    print(f"Формируем клавиатуру для {'преподавателя' if is_teacher else 'студента'}")  # Лог
    
    buttons = [
        [KeyboardButton(text="📅 Календарь")],
        [KeyboardButton(text="📚 Лекционные материалы")],
    ]
    
    if not is_teacher:
        buttons.extend([
            [KeyboardButton(text="📝 Тесты")],
            [KeyboardButton(text="📝 Домашние задания")]
        ])
    else:
        buttons.append([KeyboardButton(text="🛠 Администрирование")])
    
    print(buttons)  # Выводим структуру кнопок
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Добавить событие")],
            [KeyboardButton(text="📝 Создать тест")],
            [KeyboardButton(text="📝 Добавить ДЗ")],
            [KeyboardButton(text="📚 Добавить лекцию")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

def get_back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Назад")],
            [KeyboardButton(text="Готово")]
        ],
        resize_keyboard=True
    )

def get_yes_no_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да")],
            [KeyboardButton(text="❌ Нет")]
        ],
        resize_keyboard=True
    )

def get_tests_keyboard(tests):
    """Создает инлайн-клавиатуру для списка тестов"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for test in tests:
        try:
            # Пытаемся преобразовать строку в datetime, если это необходимо
            end_time = test[4]
            if end_time and isinstance(end_time, str):
                from datetime import datetime
                end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            
            end_time_str = end_time.strftime('%d.%m.%Y %H:%M') if end_time and hasattr(end_time, 'strftime') else "без ограничений"
            
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"{test[1]} (до {end_time_str})",
                    callback_data=f"test_{test[0]}"  # test[0] - ID теста
                )
            ])
        except Exception as e:
            continue
            
    return keyboard if keyboard.inline_keyboard else None

def get_homeworks_keyboard(homeworks):
    """Создает инлайн-клавиатуру для списка ДЗ"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for hw in homeworks:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=hw[1],  # hw[1] - название ДЗ
                callback_data=f"hw_{hw[0]}"  # hw[0] - ID задания
            )
        ])
    return keyboard if keyboard.inline_keyboard else None

def get_lectures_keyboard(lectures):
    """Создает инлайн-клавиатуру для списка лекций"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for lecture in lectures:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=lecture[1],  # lecture[1] - название лекции
                callback_data=f"lecture_{lecture[0]}"  # lecture[0] - ID лекции
            )
        ])
    return keyboard if keyboard.inline_keyboard else None