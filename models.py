from datetime import datetime
from enum import Enum

class UserRole(Enum):
    STUDENT = 'student'
    TEACHER = 'teacher'

class TestStatus(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    COMPLETED = 'completed'