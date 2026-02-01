from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename
import os
import difflib
import random
import re

from models.student_model import StudentModel
from models.fee_model import FeeModel
from models.timetable_model import TimetableModel
from models.chat_history_model import ChatHistoryModel
from models.user_context_model import UserContextModel

from utils.ai_client import client, MODEL
from utils.email_service import send_alert_email
from utils.college_info import COLLEGE_INFO
from utils.local_llm import ask_local_llm
from utils.chat_intents import INTENTS

from utils.pdf_reader import extract_pdf_chunks


chat = Blueprint("chat", __name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------------------
# FUZZY MATCH
# -------------------------------
def fuzzy_match(word, keywords, threshold=0.75):
    for key in keywords:
        if difflib.SequenceMatcher(None, word, key).ratio() >= threshold:
            return True
    return False

# -------------------------------
# INTENT DETECTION
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


    # Accept JSON OR FormData
    user_msg = request.form.get("message") or \
               (request.get_json(silent=True) or {}).get("message", "")
    user_msg = user_msg.strip()

    file = request.files.get("file")

    roll = session.get("user_roll")
    if not roll:
        return jsonify({"reply": "🔒 Please login to access your academic information."})


    # ---------------- FILE UPLOAD ----------------
    if file:
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)

        chunks = []
        if filename.lower().endswith(".pdf"):
            chunks = extract_pdf_chunks(save_path)

        session["last_uploaded_file"] = {
            "filename": filename,
            "chunks": chunks
        }

        session["file_context_pending"] = True

        return jsonify({
            "reply": (
                f"📎 File **{filename}** uploaded successfully.\n\n"
                f"I’ve read this document ({len(chunks)} sections). "
                "You can now ask questions about it."
            )
        })

    
  # ---------------- PDF QUESTION ANSWERING ----------------
    file_ctx = session.get("last_uploaded_file")

    if file_ctx and file_ctx.get("chunks") and user_msg:
        answers = []

        for chunk in file_ctx["chunks"][:5]:  # limit chunks for speed
            prompt = f"""
    Answer the question using ONLY the content below.

    CONTENT:
    {chunk}

    QUESTION:
    {user_msg}
    """
            try:
                resp = client.models.generate_content(
                    model=MODEL,
                    contents=prompt
                ).text.strip()
            except Exception:
                resp = ask_local_llm(prompt)

            answers.append(resp)

        final_prompt = "Summarize the following answers into one clear response:\n\n" + "\n\n".join(answers)

        try:
            final_reply = client.models.generate_content(
                model=MODEL,
                contents=final_prompt
            ).text.strip()
        except Exception:
            final_reply = ask_local_llm(final_prompt)

        return jsonify({"reply": final_reply})



    if not user_msg:
        return jsonify({"reply": "Please enter a message."})

    # Security block
    if re.search(r"\br\d+\b", user_msg):
        return jsonify({"reply": "🔒 I can only show your own data."})

    intents = detect_intents(user_msg)
    responses = []
    handled_intents = []

    # ---------------- ATTENDANCE ----------------
    if "ATTENDANCE" in intents:
        student = StudentModel.get_by_roll(roll)
        responses.append(f"📊 Your attendance is {student.attendance}%.")
        handled_intents.append("ATTENDANCE")
        ChatHistoryModel.save(roll, "ATTENDANCE", "DB")

    # ---------------- FEES ----------------
    if "FEES" in intents:
        fee = FeeModel.get_by_roll(roll)
        if not fee:
            responses.append("💰 No fee records found.")
        else:
            pending = fee.amount_due - fee.amount_paid
            responses.append(
                f"💰 **Fee Status**\nSemester: {fee.semester}\nDue: ₹{fee.amount_due}\nPaid: ₹{fee.amount_paid}\nPending: ₹{pending}"
            )
        handled_intents.append("FEES")
        ChatHistoryModel.save(roll, "FEES", "DB")

    # ---------------- CLASSES ----------------
    if "TODAY_CLASSES" in intents:
        classes = TimetableModel.get_today_classes()
        txt = "📅 **Today's Classes**\n" + "\n".join(
            f"- {c.start_time}-{c.end_time}: {c.subject}" for c in classes
        ) if classes else "📅 No classes today."
        responses.append(txt)
        handled_intents.append("TODAY_CLASSES")

    if "NEXT_CLASS" in intents:
        c = TimetableModel.get_next_class()
        responses.append(
            f"⏭️ Next: {c.subject} at {c.start_time}" if c else "🎉 No more classes today."
        )
        handled_intents.append("NEXT_CLASS")

    # ---------------- TIMETABLE ----------------
    if "TIMETABLE" in intents:
        timetable = TimetableModel.get_all()
        responses.append("🗓 **Timetable**\n" + "\n".join(f"- {t.day}: {t.subject}" for t in timetable))
        handled_intents.append("TIMETABLE")
        ChatHistoryModel.save(roll, "TIMETABLE", "DB")

    # ---------------- COLLEGE INFO ----------------
    if "COLLEGE_INFO" in intents:
        for k, v in COLLEGE_INFO.items():
            if k in user_msg.lower():
                responses.append(f"🏫 {v}")
                break
        handled_intents.append("COLLEGE_INFO")

    # ---------------- ELIGIBILITY ----------------
    if "ELIGIBILITY" in intents:
        _, message = StudentModel.check_eligibility(roll)
        responses.append(f"🎓 {message}")
        handled_intents.append("ELIGIBILITY")

    # ---------------- ALERTS ----------------
    if "ALERTS" in intents:
        alerts, email = StudentModel.get_alerts(roll)
        if alerts:
            responses.append("🚨 Alerts:\n" + "\n".join(alerts))
            if not session.get("alert_email_sent"):
                send_alert_email(email, alerts)
                session["alert_email_sent"] = True
        else:
            responses.append("✅ No alerts.")
        handled_intents.append("ALERTS")

    # ---------------- JOKE ----------------
    if "JOKE" in intents:
        last = session.get("last_joke_index", -1)
        choices = [i for i in range(len(JOKES)) if i != last]
        idx = random.choice(choices)
        session["last_joke_index"] = idx
        responses.append(JOKES[idx])
        handled_intents.append("JOKE")

    # ---------------- AI FALLBACK ----------------
    if not responses:
        try:
            reply = client.models.generate_content(model=MODEL, contents=user_msg).text.strip()
            source = "AI"
        except:
            reply = ask_local_llm(user_msg)
            source = "LOCAL_AI"

        ChatHistoryModel.save(roll, "GENERAL_AI", source)
        handled_intents.append("GENERAL_AI")
    else:
        reply = "\n\n".join(responses)

    # ---------------- SAVE CONTEXT ----------------
    UserContextModel.save(
        user_roll=roll,
        last_intent=handled_intents[-1],
        source="DB" if handled_intents[-1] != "GENERAL_AI" else "AI"
    )

    return jsonify({"reply": reply})
