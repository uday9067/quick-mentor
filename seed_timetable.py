from models.timetable_model import TimetableModel
import datetime

timetable_data = [
    # Monday
    {"day": "Monday", "start_time": "09:00", "end_time": "10:30", "subject": "Data Structures", "instructor": "Prof. Alice", "location": "Room 101"},
    {"day": "Monday", "start_time": "10:45", "end_time": "12:15", "subject": "Database Systems", "instructor": "Prof. Bob", "location": "Room 102"},
    {"day": "Monday", "start_time": "13:00", "end_time": "14:30", "subject": "Software Engineering", "instructor": "Prof. Charlie", "location": "Room 103"},
    
    # Tuesday
    {"day": "Tuesday", "start_time": "09:00", "end_time": "10:30", "subject": "Algorithms", "instructor": "Prof. Dave", "location": "Room 104"},
    {"day": "Tuesday", "start_time": "10:45", "end_time": "12:15", "subject": "Computer Networks", "instructor": "Prof. Eve", "location": "Room 201"},
    {"day": "Tuesday", "start_time": "13:00", "end_time": "14:30", "subject": "Operating Systems", "instructor": "Prof. Frank", "location": "Room 202"},
    # An evening class for testing the "next lecture" query right now
    {"day": "Tuesday", "start_time": "17:30", "end_time": "19:00", "subject": "AI Project Lab", "instructor": "Prof. Grace", "location": "Lab 3"},

    # Wednesday
    {"day": "Wednesday", "start_time": "09:00", "end_time": "10:30", "subject": "Machine Learning", "instructor": "Prof. Heidi", "location": "Room 101"},
    {"day": "Wednesday", "start_time": "10:45", "end_time": "12:15", "subject": "Cloud Computing", "instructor": "Prof. Smith", "location": "Room 102"},
    {"day": "Wednesday", "start_time": "13:00", "end_time": "14:30", "subject": "Cyber Security", "instructor": "Prof. Sanjeev", "location": "Room 303"},

    # Thursday
    {"day": "Thursday", "start_time": "09:00", "end_time": "10:30", "subject": "Data Structures", "instructor": "Prof. Alice", "location": "Room 101"},
    {"day": "Thursday", "start_time": "10:45", "end_time": "12:15", "subject": "Database Systems", "instructor": "Prof. Bob", "location": "Room 102"},
    {"day": "Thursday", "start_time": "13:00", "end_time": "14:30", "subject": "Mathematics IV", "instructor": "Prof. Smith", "location": "Room 103"},

    # Friday
    {"day": "Friday", "start_time": "09:00", "end_time": "10:30", "subject": "Web Technologies", "instructor": "Prof. Charlie", "location": "Room 104"},
    {"day": "Friday", "start_time": "10:45", "end_time": "12:15", "subject": "Internet of Things", "instructor": "Prof. Eve", "location": "Room 201"},
    {"day": "Friday", "start_time": "13:00", "end_time": "14:30", "subject": "Mini Project", "instructor": "Prof. Frank", "location": "Lab 1"},
]

from utils.db import engine
from sqlalchemy import text

# Clear existing timetable
with engine.connect() as conn:
    conn.execute(text("TRUNCATE TABLE timetable"))
    conn.commit()

today_date = datetime.datetime.now().date()

for entry in timetable_data:
    TimetableModel.create(
        day=entry["day"],
        class_date=today_date, # Fallback, TimetableModel.create handles this
        start_time=entry["start_time"],
        end_time=entry["end_time"],
        subject=entry["subject"],
        instructor=entry["instructor"],
        location=entry["location"]
    )

print("Successfully seeded timetable!")
