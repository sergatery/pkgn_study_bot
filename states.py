from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    waiting_for_event_title = State()
    waiting_for_event_description = State()
    waiting_for_event_date = State()
    waiting_for_test_title = State()
    waiting_for_test_description = State()
    waiting_for_test_questions = State()
    waiting_for_test_start_time = State()
    waiting_for_test_end_time = State()
    waiting_for_hw_title = State()
    waiting_for_hw_description = State()
    waiting_for_lecture_title = State()
    waiting_for_lecture_description = State()
    waiting_for_lecture_content = State()
    waiting_for_question_text = State()
    waiting_for_question_options = State()
    waiting_for_question_correct = State()
    waiting_for_more_questions = State()

class TestStates(StatesGroup):
    taking_test = State()

class HomeworkStates(StatesGroup):
    waiting_for_homework = State()