from utils.db import engine
from sqlalchemy import text
import uuid
from datetime import datetime


class ChatModel:

    @staticmethod
    def create_table():
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chats (
                    id VARCHAR(36) PRIMARY KEY,
                    user_roll VARCHAR(50) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    timestamps DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()

    @staticmethod
    def create(name, user_roll):
        chat_id = str(uuid.uuid4())
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO chats (id, user_roll, name, timestamps)
                VALUES (:id, :user_roll, :name, :timestamps)
            """), {
                "id": chat_id,
                "user_roll": user_roll,
                "name": name,
                "timestamps": datetime.now()
            })
            conn.commit()
        return chat_id

    @staticmethod
    def get_all_by_user(user_roll):
        with engine.connect() as conn:
            return conn.execute(
                text("SELECT * FROM chats WHERE user_roll = :roll ORDER BY timestamps DESC"),
                {"roll": user_roll}
            ).fetchall()

    @staticmethod
    def get_all():
        with engine.connect() as conn:
            return conn.execute(text("SELECT * FROM chats ORDER BY timestamps DESC")).fetchall()

    @staticmethod
    def get_by_id(chat_id):
        with engine.connect() as conn:
            return conn.execute(
                text("SELECT * FROM chats WHERE id = :id"),
                {"id": chat_id}
            ).fetchone()

    @staticmethod
    def delete(chat_id):
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM chats WHERE id = :id"), {"id": chat_id})
            conn.commit()
    @staticmethod
    def update_name(chat_id, name):
        with engine.connect() as conn:
            conn.execute(
                text("UPDATE chats SET name = :name WHERE id = :id"),
                {"name": name, "id": chat_id}
            )
            conn.commit()
