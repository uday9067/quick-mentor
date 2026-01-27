from utils.db import engine
from sqlalchemy import text

class UserContextModel:

    @staticmethod
    def get(user_roll):
        query = text("""
            SELECT last_intent, last_source
            FROM user_context
            WHERE user_roll = :roll
        """)

        with engine.connect() as conn:
            return conn.execute(query, {"roll": user_roll}).fetchone()

    @staticmethod
    def save(user_roll, last_intent, source):
        query = text("""
            INSERT INTO user_context (user_roll, last_intent, last_source)
            VALUES (:roll, :intent, :source)
            ON DUPLICATE KEY UPDATE
                last_intent = :intent,
                last_source = :source,
                updated_at = CURRENT_TIMESTAMP
        """)

        with engine.connect() as conn:
            conn.execute(query, {
                "roll": user_roll,
                "intent": last_intent,
                "source": source
            })
            conn.commit()
