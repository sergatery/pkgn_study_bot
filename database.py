import sqlite3
from datetime import datetime
from aiogram.types import Message
from config import Config
import os
os.environ['TZ'] = 'Asia/Novosibirsk'  
def init_db():
    conn = sqlite3.connect('student_assistant.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        role TEXT CHECK(role IN ('student', 'teacher')) NOT NULL DEFAULT 'student',
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Calendar events table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS calendar_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        event_date DATE NOT NULL,
        created_by INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users (user_id)
    )
    ''')
    
    # Tests table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tests (
        test_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        questions TEXT NOT NULL,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        created_by INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users (user_id)
    )
    ''')
    
    # Test results table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS test_results (
        result_id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        answers TEXT NOT NULL,
        score INTEGER,
        total_questions INTEGER NOT NULL, 
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (test_id) REFERENCES tests (test_id),
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')
    
    # Homework table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS homework (
        hw_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        created_by INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users (user_id)
    )
    ''')
    
    # Homework submissions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS homework_submissions (
        submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
        hw_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        message TEXT,
        file_id TEXT,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (hw_id) REFERENCES homework (hw_id),
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')
    
    # Lecture materials table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lecture_materials (
        material_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        created_by INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users (user_id)
    )
    ''')
    
    # Lecture content table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lecture_content (
        content_id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_id INTEGER NOT NULL,
        message TEXT,
        file_id TEXT,
        file_type TEXT,
        order_num INTEGER NOT NULL,
        FOREIGN KEY (material_id) REFERENCES lecture_materials (material_id)
    )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    return sqlite3.connect('student_assistant.db')