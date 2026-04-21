from models.student_model import StudentModel
from models.fee_model import FeeModel
from models.timetable_model import TimetableModel
from utils.college_info import COLLEGE_INFO, FEES_FACULTY_CONTACT, CLASS_TEACHERS, FACULTY_DB, ADMISSION_CONTACT
from utils.ai_client import client, MODEL
from utils.local_llm import ask_local_llm
from datetime import datetime


def is_college_related(query):
    classification_prompt = f"""
Classify the following user query as either "COLLEGE_RELATED" or "GENERAL".

COLLEGE_RELATED includes queries about:
- Attendance, fees, grades, marks, results
- Timetable, classes, lectures, schedule
- Faculty, teachers, professors, staff
- Admission, enrollment, eligibility
- College policies, rules, exams, library
- Student personal information (your attendance, your fees, your timetable, your marks, etc.)
- Any academic or administrative matter related to the college

GENERAL includes queries about:
- General knowledge questions
- Casual conversation, greetings
- Jokes, entertainment
- Help with non-academic tasks
- Math problems, coding help (unrelated to college)
- Weather, news, etc.

Respond with ONLY one word: COLLEGE_RELATED or GENERAL

Query: {query}
"""
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=classification_prompt
        ).text.strip().upper()
        
        if "GENERAL" in response:
            return False
        return True
    except:
        try:
            response = ask_local_llm(classification_prompt).strip().upper()
            if "GENERAL" in response:
                return False
            return True
        except:
            return True


def get_student_context(roll):
    student = StudentModel.get_by_roll(roll)
    if not student:
        return "No student record found."

    fee = FeeModel.get_by_roll(roll)
    today_classes = TimetableModel.get_today_classes()
    next_class = TimetableModel.get_next_class()
    
    context_parts = [
        "=== STUDENT PERSONAL INFORMATION ===",
        f"Name: {student.name}",
        f"Roll Number: {student.roll}",
        f"Department: {student.department}",
        f"Year: {student.year}",
        f"Email: {student.email}",
        f"Attendance: {student.attendance}%",
    ]

    if fee:
        pending = fee.amount_due - fee.amount_paid
        context_parts.extend([
            "",
            "=== FEE DETAILS ===",
            f"Semester: {fee.semester}",
            f"Amount Due: ₹{fee.amount_due}",
            f"Amount Paid: ₹{fee.amount_paid}",
            f"Pending: ₹{pending}",
            f"Due Date: {fee.due_date}",
        ])
    else:
        context_parts.extend(["", "=== FEE DETAILS ===", "No fee records found."])

    if today_classes:
        context_parts.extend([
            "",
            "=== TODAY'S CLASSES ===",
        ])
        for c in today_classes:
            context_parts.append(f"- {c.start_time}-{c.end_time}: {c.subject} (Room: {c.location}, Instructor: {c.instructor})")
    else:
        context_parts.extend(["", "=== TODAY'S CLASSES ===", "No classes scheduled for today."])

    if next_class:
        context_parts.extend([
            "",
            "=== NEXT CLASS ===",
            f"Subject: {next_class.subject}",
            f"Time: {next_class.start_time} to {next_class.end_time}",
            f"Location: {next_class.location}",
            f"Instructor: {next_class.instructor}",
        ])

    eligible, eligibility_msg = StudentModel.check_eligibility(roll)
    context_parts.extend([
        "",
        "=== EXAM ELIGIBILITY ===",
        eligibility_msg,
    ])

    alerts, _ = StudentModel.get_alerts(roll)
    if alerts:
        context_parts.extend([
            "",
            "=== ALERTS ===",
        ])
        context_parts.extend(alerts)

    if student.department and student.year:
        class_teacher = CLASS_TEACHERS.get((student.department, student.year), CLASS_TEACHERS["DEFAULT"])
        context_parts.extend([
            "",
            "=== CLASS TEACHER ===",
            f"Your class teacher: {class_teacher}",
        ])

    return "\n".join(context_parts)


def get_college_context():
    context_parts = [
        "=== COLLEGE GENERAL INFORMATION ===",
    ]

    for key, value in COLLEGE_INFO.items():
        context_parts.append(f"{key.capitalize()}: {value}")

    context_parts.extend([
        "",
        "=== IMPORTANT CONTACTS ===",
        f"Fees Department: {FEES_FACULTY_CONTACT}",
        f"Admission Office: {ADMISSION_CONTACT}",
    ])

    context_parts.extend([
        "",
        "=== FACULTY DIRECTORY ===",
    ])
    for key, details in FACULTY_DB.items():
        context_parts.append(f"- {details['name']}: {details['designation']}, {details['department']}, Cabin: {details['cabin']}, Contact: {details['contact']}")

    return "\n".join(context_parts)


def generate_college_response(query, roll):
    student_context = get_student_context(roll)
    college_context = get_college_context()

    system_prompt = f"""You are a helpful college assistant chatbot. You have access to the student's personal information and college database.

Your task is to answer the user's query based ONLY on the provided context. If the information is not available in the context, say so honestly. Do not make up information.

Be conversational and natural - not robotic or template-like. Provide complete, helpful answers.

{student_context}

{college_context}

User Query: {query}

Provide a natural, helpful response:"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=system_prompt
        ).text.strip()
        return response, "AI_COLLEGE"
    except:
        try:
            response = ask_local_llm(system_prompt)
            return response, "LOCAL_AI_COLLEGE"
        except:
            return "I'm having trouble connecting to the AI service. Please try again later.", "ERROR"


def generate_general_response(query):
    system_prompt = f"""You are a helpful, friendly chatbot assistant. 

User says: {query}

Respond naturally and helpfully. If you don't know something, be honest about it. Keep your response conversational and not too long."""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=system_prompt
        ).text.strip()
        return response, "AI_GENERAL"
    except:
        try:
            response = ask_local_llm(system_prompt)
            return response, "LOCAL_AI_GENERAL"
        except:
            return "I'm here to help! Could you rephrase your question?", "ERROR"
