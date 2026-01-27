from utils.db import engine
from sqlalchemy import text


class ChatHistoryModel:

    @staticmethod
    def save(user_roll, intent, source):
        query = text("""
            INSERT INTO chat_history (user_roll, intent, source)
            VALUES (:roll, :intent, :source)
        """)

        with engine.connect() as conn:
            conn.execute(query, {
                "roll": user_roll,
                "intent": intent,
                "source": source
            })
            conn.commit()


    @staticmethod
    def get_user_history(user_roll, limit=10):
        query = text("""
            SELECT user_message, bot_reply
            FROM chat_history
            WHERE user_roll = :roll
            ORDER BY created_at DESC
            LIMIT :limit
        """)

        with engine.connect() as conn:
            return conn.execute(query, {
                "roll": user_roll,
                "limit": limit
            }).fetchall()

    @staticmethod
    def get_recent(limit=100):
            from utils.db import engine
            from sqlalchemy import text

            with engine.connect() as conn:
                q = text("""
                    SELECT user_roll, intent, source, created_at
                    FROM chat_history
                    ORDER BY created_at DESC
                    LIMIT :limit
                """)
                return conn.execute(q, {"limit": limit}).fetchall()

