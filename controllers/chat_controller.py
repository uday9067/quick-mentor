from flask import Blueprint, request, jsonify, session
from models.student_model import StudentModel
from models.fee_model import FeeModel
from models.timetable_model import TimetableModel
from models.chat_history_model import ChatHistoryModel
from models.user_context_model import UserContextModel

from utils.ai_client import client, MODEL
from utils.email_service import send_alert_email
from utils.college_info import COLLEGE_INFO
from utils.local_llm import ask_local_llm
from utils.chat_intents import INTENTS, FUZZY_THRESHOLD

import difflib
import random
import re

chat = Blueprint("chat", __name__)

# -------------------------------
# FUZZY MATCH HELPER
# -------------------------------
def fuzzy_match(word, keywords, threshold=0.75):
    for key in keywords:
        if difflib.SequenceMatcher(None, word, key).ratio() >= threshold:
            return True
    return False

# -------------------------------
# MULTI-INTENT DETECTOR
# -------------------------------
def detect_intents(msg):
    msg = msg.lower()
    found = []

    for intent, meta in INTENTS.items():
        for k in meta.get("keywords", []):
            if k in msg:
                found.append(intent)
                break

        for p in meta.get("phrases", []):
            if p in msg:
                found.append(intent)
                break

    return list(set(found))

# -------------------------------
# JOKES
# -------------------------------
JOKES = [
    "😂 Why don’t scientists trust atoms? Because they make up everything!",
    "😂 Why do programmers prefer dark mode? Because light attracts bugs.",
    "😂 Why was the math book sad? It had too many problems.",
    "😂 Why did the computer go to the doctor? Because it caught a virus!",
    "😂 Why did the developer go broke? Because he used up all his cache!"
]

# -------------------------------
# CHAT ROUTE
# -------------------------------
@chat.route("/get_response", methods=["POST"])
def get_response():

    data = request.get_json()
    user_msg = data.get("message", "").strip()

    if not user_msg:
        return jsonify({"reply": "Please enter a message."})

    roll = session.get("user_roll")
    if not roll:
        return jsonify({"reply": "🔒 Please login to access your academic information."})

    msg = user_msg.lower()
    responses = []
    handled_intents = []

    # -------------------------------
    # SECURITY BLOCK (IMMEDIATE EXIT)
    # -------------------------------
    if re.search(r"\br\d+\b", msg):
        return jsonify({
            "reply": "🔒 For security reasons, I can only show your own data."
        })

    intents = detect_intents(user_msg)

    # -------------------------------
    # ATTENDANCE
    # -------------------------------
    if "ATTENDANCE" in intents:
        student = StudentModel.get_by_roll(roll)
        responses.append(f"📊 Your attendance is {student.attendance}%.")
        handled_intents.append("ATTENDANCE")
        ChatHistoryModel.save(roll, "ATTENDANCE", "DB")

    # -------------------------------
    # FEES
    # -------------------------------
    if "FEES" in intents:
        fee = FeeModel.get_by_roll(roll)
        if not fee:
            responses.append("💰 No fee records found for you.")
        else:
            pending = fee.amount_due - fee.amount_paid
            responses.append(
                "💰 **Your Fee Status**\n"
                f"- Semester: {fee.semester}\n"
                f"- Total Due: ₹{fee.amount_due}\n"
                f"- Paid: ₹{fee.amount_paid}\n"
                f"- Pending: ₹{pending}\n"
                f"- Due Date: {fee.due_date}"
            )
        handled_intents.append("FEES")
        ChatHistoryModel.save(roll, "FEES", "DB")

    # -------------------------------
    # TODAY'S CLASSES
    # -------------------------------
    if "TODAY_CLASSES" in intents:
        classes = TimetableModel.get_today_classes()
        if not classes:
            responses.append("📅 You have no classes scheduled today.")
        else:
            txt = "📅 **Today's Classes**\n"
            for c in classes:
                txt += f"- {c.start_time}–{c.end_time}: {c.subject}\n"
            responses.append(txt)
        handled_intents.append("TODAY_CLASSES")

    # -------------------------------
    # NEXT CLASS
    # -------------------------------
    if "NEXT_CLASS" in intents:
        c = TimetableModel.get_next_class()
        if not c:
            responses.append("🎉 You have no more classes today.")
        else:
            responses.append(
                "⏭️ **Your Next Class**\n"
                f"- {c.subject}\n"
                f"- Time: {c.start_time}–{c.end_time}\n"
                f"- Instructor: {c.instructor}\n"
                f"- Location: {c.location}"
            )
        handled_intents.append("NEXT_CLASS")

    # -------------------------------
    # TIMETABLE
    # -------------------------------
    if "TIMETABLE" in intents:
        timetable = TimetableModel.get_all()
        if not timetable:
            responses.append("🗓 No timetable entries found.")
        else:
            txt = "🗓 **Your Timetable**\n"
            for t in timetable:
                txt += f"- {t.day}: {t.subject} ({t.start_time}-{t.end_time})\n"
            responses.append(txt)
        handled_intents.append("TIMETABLE")
        ChatHistoryModel.save(roll, "TIMETABLE", "DB")

    # -------------------------------
    # COLLEGE INFO
    # -------------------------------
    if "COLLEGE_INFO" in intents:
        for k, v in COLLEGE_INFO.items():
            if k in msg:
                responses.append(f"🏫 {v}")
                break
        handled_intents.append("COLLEGE_INFO")
        ChatHistoryModel.save(roll, "COLLEGE_INFO", "FAQ")

    # -------------------------------
    # ELIGIBILITY
    # -------------------------------
    if "ELIGIBILITY" in intents:
        _, message = StudentModel.check_eligibility(roll)
        responses.append(f"🎓 {message}")
        handled_intents.append("ELIGIBILITY")
        ChatHistoryModel.save(roll, "ELIGIBILITY", "DB")

    # -------------------------------
    # ALERTS
    # -------------------------------
    if "ALERTS" in intents:
        alerts, email = StudentModel.get_alerts(roll)
        if not alerts:
            responses.append("✅ No alerts. Everything looks good!")
        else:
            txt = "🚨 **Important Alerts**\n"
            for a in alerts:
                txt += f"- {a}\n"
            responses.append(txt)

            if not session.get("alert_email_sent"):
                send_alert_email(email, alerts)
                session["alert_email_sent"] = True

        handled_intents.append("ALERTS")
        ChatHistoryModel.save(roll, "ALERTS", "DB")

    # -------------------------------
    # JOKES
    # -------------------------------
    if "JOKE" in intents:
        last = session.get("last_joke_index", -1)
        available = [i for i in range(len(JOKES)) if i != last]
        idx = random.choice(available)
        session["last_joke_index"] = idx
        responses.append(JOKES[idx])
        handled_intents.append("JOKE")
        ChatHistoryModel.save(roll, "JOKE", "FUN")

    # -------------------------------
    # AI FALLBACK
    # -------------------------------
    if not responses:
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=user_msg
            )
            reply = response.text.strip()
        except Exception:
            reply = ask_local_llm(user_msg)
            source = "AI"

        handled_intents.append("GENERAL_AI")

        # ✅ LOG AI CHAT
        ChatHistoryModel.save(
            roll,
            "GENERAL_AI",
            source
        )
    else:
        reply = "\n\n".join(responses)


    # -------------------------------
    # SAVE CONTEXT
    # -------------------------------
    UserContextModel.save(
        user_roll=roll,
        last_intent=handled_intents[-1],
        source="DB" if handled_intents[-1] != "GENERAL_AI" else "AI"
    )

    return jsonify({"reply": reply})
