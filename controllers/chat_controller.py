from models.message_model import MessageModel
from models.chat_model import ChatModel
from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename
import os
import re

from models.chat_history_model import ChatHistoryModel
from models.user_context_model import UserContextModel

from utils.ai_client import client, MODEL
from utils.local_llm import ask_local_llm
from utils.query_classifier import is_college_related, generate_college_response, generate_general_response

from utils.pdf_reader import extract_pdf_chunks


chat = Blueprint("chat", __name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@chat.route("/get_response", methods=["POST"])
def get_response():

    user_msg = request.form.get("message") or \
               (request.get_json(silent=True) or {}).get("message", "")
    user_msg = user_msg.strip()

    file = request.files.get("file")
    chatId = request.form.get("chatId") or \
                (request.get_json(silent=True) or {}).get("chatId", "")
    chatId = chatId.strip() if chatId else ""

    roll = session.get("user_roll")
    if not roll:
        return jsonify({"reply": "🔒 Please login to access your academic information."})

    if user_msg.lower() == "/activity":
        rows = ChatHistoryModel.get_user_activity(roll, limit=5)

        if not rows:
            return jsonify({"reply": "ℹ️ No recent activity found."})

        reply = "🕘 **Your recent activity:**\n\n"

        for r in rows:
            intent = r.intent.replace("_", " ").title()
            reply += f"• {intent} ({r.source})\n"

        ChatHistoryModel.save(
            user_roll=roll,
            intent="VIEW_ACTIVITY",
            source="SYSTEM"
        )

        return jsonify({"reply": reply})

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
                f"I've read this document ({len(chunks)} sections). "
                "You can now ask questions about it."
            )
        })

    file_ctx = session.get("last_uploaded_file")

    if file_ctx and file_ctx.get("chunks") and user_msg:
        answers = []

        for chunk in file_ctx["chunks"][:5]:
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

        if chatId:
            # Check if chat needs renaming (first interaction)
            existing_msgs = MessageModel.get_by_chat_id(chatId)
            if len(existing_msgs) == 0:
                new_name = (user_msg[:30] + "...") if len(user_msg) > 30 else user_msg
                ChatModel.update_name(chatId, new_name)

            MessageModel.create(userId=roll, chatId=chatId, content=user_msg, isResponse=False)
            MessageModel.create(userId=roll, chatId=chatId, content=final_reply, isResponse=True)
        return jsonify({"reply": final_reply, "chatId": chatId})

    if not user_msg:
        return jsonify({"reply": "Please enter a message."})

    if re.search(r"\br\d+\b", user_msg):
        return jsonify({"reply": "🔒 I can only show your own data."})

    try:
        college_related = is_college_related(user_msg)
    except:
        college_related = True

    if college_related:
        reply, source = generate_college_response(user_msg, roll)
    else:
        reply, source = generate_general_response(user_msg)

    ChatHistoryModel.save(roll, "QUERY", source)
    UserContextModel.save(
        user_roll=roll,
        last_intent="QUERY",
        source=source
    )

    if chatId:
        # Check if chat needs renaming (first message)
        existing_msgs = MessageModel.get_by_chat_id(chatId)
        if len(existing_msgs) == 0: # This is the first message (we haven't saved it yet)
            new_name = (user_msg[:30] + "...") if len(user_msg) > 30 else user_msg
            ChatModel.update_name(chatId, new_name)
        
        MessageModel.create(userId=roll, chatId=chatId, content=user_msg, isResponse=False)
        MessageModel.create(userId=roll, chatId=chatId, content=reply, isResponse=True)

    return jsonify({"reply": reply, "chatId": chatId})


# ─── Chat CRUD API ───────────────────────────────────────────────────────────

@chat.route("/api/chats", methods=["GET"])
def list_chats():
    roll = session.get("user_roll")
    if not roll:
        return jsonify({"error": "Unauthorized"}), 401
    rows = ChatModel.get_all_by_user(roll)
    return jsonify([{"id": r.id, "name": r.name, "timestamps": str(r.timestamps)} for r in rows])


@chat.route("/api/chats", methods=["POST"])
def create_chat():
    roll = session.get("user_roll")
    if not roll:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    name = data.get("name", "New Chat").strip() or "New Chat"
    chat_id = ChatModel.create(name=name, user_roll=roll)
    return jsonify({"id": chat_id, "name": name}), 201


@chat.route("/api/chats/<chat_id>/messages", methods=["GET"])
def get_chat_messages(chat_id):
    roll = session.get("user_roll")
    if not roll:
        return jsonify({"error": "Unauthorized"}), 401
    rows = MessageModel.get_by_chat_id(chat_id)
    return jsonify([{
        "id": r.id,
        "content": r.content,
        "isResponse": bool(r.isResponse),
        "timestamps": str(r.timestamps)
    } for r in rows])


@chat.route("/api/chats/<chat_id>", methods=["DELETE"])
def delete_chat(chat_id):
    roll = session.get("user_roll")
    if not roll:
        return jsonify({"error": "Unauthorized"}), 401
    ChatModel.delete(chat_id)
    return jsonify({"ok": True})


@chat.route("/api/chats/<chat_id>/rename", methods=["POST"])
def rename_chat(chat_id):
    roll = session.get("user_roll")
    if not roll:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json(silent=True) or {}
    new_name = data.get("name", "").strip()
    if not new_name:
        return jsonify({"error": "Name cannot be empty"}), 400
    
    ChatModel.update_name(chat_id, new_name)
    return jsonify({"ok": True, "name": new_name})
