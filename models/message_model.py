from utils.db import engine
from sqlalchemy import text
import uuid
from datetime import datetime

class MessageModel:

    @staticmethod
    def create_table():
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS messages (
                    id VARCHAR(36) PRIMARY KEY,
                    seq BIGINT AUTO_INCREMENT,
                    userId VARCHAR(255) NOT NULL,
                    isResponse BOOLEAN NOT NULL DEFAULT FALSE,
                    chatId VARCHAR(36) NOT NULL,
                    content TEXT NOT NULL,
                    timestamps DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chatId) REFERENCES chats(id) ON DELETE CASCADE,
                    KEY idx_seq (seq)
                )
            """))
            # Migration: add seq column to existing tables that don't have it
            try:
                conn.execute(text("""
                    ALTER TABLE messages
                    ADD COLUMN seq BIGINT AUTO_INCREMENT,
                    ADD KEY idx_seq (seq)
                """))
                conn.commit()
            except Exception:
                pass  # column already exists, skip migration

    @staticmethod
    def create(userId, chatId, content, isResponse=False):
        message_id = str(uuid.uuid4())
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO messages (id, userId, isResponse, chatId, content, timestamps)
                VALUES (:id, :userId, :isResponse, :chatId, :content, :timestamps)
            """), {
                "id": message_id,
                "userId": userId,
                "isResponse": isResponse,
                "chatId": chatId,
                "content": content,
                "timestamps": datetime.now().isoformat()
            })
            conn.commit()
        return message_id

    @staticmethod
    def get_by_chat_id(chatId):
        with engine.connect() as conn:
            return conn.execute(text("""
                SELECT * FROM messages 
                WHERE chatId = :chatId
                ORDER BY seq ASC
            """), {"chatId": chatId}).fetchall()

    @staticmethod
    def get_by_id(message_id):
        with engine.connect() as conn:
            return conn.execute(text("SELECT * FROM messages WHERE id = :id"), {"id": message_id}).fetchone()

    @staticmethod
    def delete(message_id):
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM messages WHERE id = :id"), {"id": message_id})
            conn.commit()
