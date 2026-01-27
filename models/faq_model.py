from utils.db import engine
from sqlalchemy import text


class FAQModel:
    """
    Handles institutional / official Q&A.
    AI should NEVER answer these.
    """

    @staticmethod
    def get_all_active():
        """
        Fetch all active institutional knowledge.
        """
        query = text("""
            SELECT id, category, question, answer, keywords
            FROM institutional_knowledge
            WHERE is_active = TRUE
        """)

        with engine.connect() as conn:
            return conn.execute(query).fetchall()

    @staticmethod
    def find_answer(user_question: str):
        """
        Match user question against stored keywords.
        Returns official answer if found, else None.
        """

        if not user_question:
            return None

        user_q = user_question.lower()

        query = text("""
            SELECT answer, keywords
            FROM institutional_knowledge
            WHERE is_active = TRUE
        """)

        with engine.connect() as conn:
            rows = conn.execute(query).fetchall()

        for row in rows:
            keywords = row.keywords.lower().split(",")

            for key in keywords:
                if key.strip() and key.strip() in user_q:
                    return row.answer

        return None
