# models/fee_model.py
from utils.db import engine
from sqlalchemy import text

class FeeModel:

    @staticmethod
    def get_all():
        with engine.connect() as conn:
            q = text("""
            SELECT 
                f.id,
                f.roll,
                s.name AS student_name,
                f.semester,
                f.amount_due,
                f.amount_paid,
                f.due_date
            FROM fees f
            JOIN students s ON f.roll = s.roll
        """)
            return conn.execute(q).fetchall()

    @staticmethod
    def get_by_roll(roll):
        with engine.connect() as conn:
            q = text("SELECT * FROM fees WHERE roll = :roll")
            return conn.execute(q, {"roll": roll}).fetchone()

    @staticmethod
    def create(roll, semester, amount_due, amount_paid, due_date):
        with engine.connect() as conn:
            q = text("""
                INSERT INTO fees (roll, semester, amount_due, amount_paid, due_date)
                VALUES (:roll, :semester, :amount_due, :amount_paid, :due_date)
            """)
            conn.execute(q, {
                "roll": roll,
                "semester": int(semester or 1),
                "amount_due": float(amount_due or 0),
                "amount_paid": float(amount_paid or 0),
                "due_date": due_date
            })
            conn.commit()

    @staticmethod
    def delete(fid):
        with engine.connect() as conn:
            q = text("DELETE FROM fees WHERE id = :id")
            conn.execute(q, {"id": fid})
            conn.commit()

    @staticmethod
    def update(fid, semester, amount_due, amount_paid, due_date):
        with engine.connect() as conn:
            q = text("""
                UPDATE fees
                SET semester = :sem,
                    amount_due = :due,
                    amount_paid = :paid,
                    due_date = :date
                WHERE id = :id
            """)
            conn.execute(q, {
                "id": fid,
                "sem": semester,
                "due": amount_due,
                "paid": amount_paid,
                "date": due_date
            })
            conn.commit()

    @staticmethod
    def count():
        with engine.connect() as conn:
            q = text("SELECT COUNT(*) FROM fees")
            return conn.execute(q).scalar()
        

    @staticmethod
    def get_pending_fee_students():
        with engine.connect() as conn:
            return conn.execute(
                text("""
                    SELECT s.roll, s.name, f.semester,
                        (f.amount_due - f.amount_paid) AS pending_amount,
                        f.due_date
                    FROM students s
                    JOIN fees f ON s.roll = f.roll
                    WHERE (f.amount_due - f.amount_paid) > 0
                    ORDER BY pending_amount DESC
                """)
            ).fetchall()


    @staticmethod
    def exists_for_roll_semester(roll, semester):
        with engine.connect() as conn:
            q = text("""
                SELECT COUNT(*) 
                FROM fees 
                WHERE roll = :roll AND semester = :semester
            """)
            return conn.execute(q, {
                "roll": roll,
                "semester": semester
            }).scalar() > 0
