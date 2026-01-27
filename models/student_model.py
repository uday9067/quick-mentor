# models/student_model.py
from utils.db import engine
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


class StudentModel:

    @staticmethod
    def get_by_roll(roll):
        with engine.connect() as conn:
            q = text("SELECT * FROM students WHERE roll = :roll")
            return conn.execute(q, {"roll": roll}).fetchone()


    @staticmethod
    def get_all():
        with engine.connect() as conn:
            q = text("""
                SELECT id, roll, name, department, year, attendance, email
                FROM students
                ORDER BY CAST(roll AS UNSIGNED)
            """)
            return conn.execute(q).fetchall()



    @staticmethod
    def create(roll, name, department, year, email, password, attendance=0):
        try:
            with engine.connect() as conn:
                q = text("""
                    INSERT INTO students
                    (roll, name, department, year, attendance, email, password)
                    VALUES (:roll, :name, :department, :year, :attendance, :email, :password)
                """)
                conn.execute(q, {
                "roll": roll,
                "name": name,
                "department": department,
                "year": int(year or 1),
                "attendance": float(attendance or 0),
                "email": email,
                "password": password,
                })
                conn.commit()
            return True

        except IntegrityError:
            return False


    @staticmethod
    def delete(student_id):
        with engine.connect() as conn:
            q = text("DELETE FROM students WHERE id = :id")
            conn.execute(q, {"id": student_id})
            conn.commit()

    @staticmethod
    def update_admin(sid, name, department, year, attendance, email):
        with engine.connect() as conn:
            q = text("""
                UPDATE students
                SET name = :name,
                    department = :dept,
                    year = :year,
                    attendance = :att,
                    email = :email
                WHERE id = :id
            """)
            conn.execute(q, {
                "id": sid,
                "name": name,
                "dept": department,
                "year": year,
                "att": attendance,
                "email": email
            })
            conn.commit()

    @staticmethod
    def count():
        with engine.connect() as conn:
            q = text("SELECT COUNT(*) FROM students")
            return conn.execute(q).scalar()

    @staticmethod
    def get_by_email(email):
        with engine.connect() as conn:
            q = text("SELECT * FROM students WHERE email = :email")
            return conn.execute(q, {"email": email}).fetchone()

    @staticmethod
    def update_password(email, new_password):
        with engine.connect() as conn:
            q = text("UPDATE students SET password = :p WHERE email = :email")
            conn.execute(q, {"p": new_password, "email": email})
            conn.commit()
    
    @staticmethod
    def update_user_profile(roll, name, email):
        try:
            with engine.connect() as conn:
                q = text("""
                    UPDATE students
                    SET name = :name,
                        email = :email
                    WHERE roll = :roll
                """)
                conn.execute(q, {
                    "roll": roll,
                    "name": name,
                    "email": email
                })
                conn.commit()
            return True

        except Exception as e:
            print("Profile update failed:", e)
            return False

    @staticmethod
    def update_email(roll, new_email):
        query = text("UPDATE students SET email = :email WHERE roll = :roll")
        with engine.connect() as conn:
            conn.execute(query, {"email": new_email, "roll": roll})
            conn.commit()

    

    @staticmethod
    def check_eligibility(roll):
        with engine.connect() as conn:
            student = conn.execute(
                text("SELECT attendance FROM students WHERE roll = :r"),
                {"r": roll}
            ).fetchone()

            fee = conn.execute(
                text("SELECT amount_due, amount_paid FROM fees WHERE roll = :r"),
                {"r": roll}
            ).fetchone()

        if not student:
            return False, "Student record not found."

        attendance_ok = student.attendance >= 75

        pending = 0
        if fee:
            pending = fee.amount_due - fee.amount_paid

        if attendance_ok and pending == 0:
            return True, "You are eligible for exams."

        reason = []
        if not attendance_ok:
            reason.append("attendance is below 75%")
        if pending > 0:
            reason.append(f"₹{pending} fee is pending")

        return False, "You are NOT eligible because " + " and ".join(reason)
    
    @staticmethod
    def get_alerts(roll):
        alerts = []

        with engine.connect() as conn:
            student = conn.execute(
                text("SELECT attendance, email FROM students WHERE roll = :r"),
                {"r": roll}
            ).fetchone()

            fee = conn.execute(
                text("SELECT amount_due, amount_paid, due_date FROM fees WHERE roll = :r"),
                {"r": roll}
            ).fetchone()

        if student.attendance < 75:
            alerts.append(f"⚠️ Your attendance is low ({student.attendance}%).")

        if fee:
            pending = fee.amount_due - fee.amount_paid
            if pending > 0:
                alerts.append(f"⚠️ You have ₹{pending} fee pending. Due date: {fee.due_date}")

        return alerts, student.email

    @staticmethod
    def get_low_attendance_students(threshold=75):
        with engine.connect() as conn:
            return conn.execute(
                text("""
                    SELECT roll, name, department, year, attendance
                    FROM students
                    WHERE attendance < :threshold
                    ORDER BY attendance ASC
                """),
                {"threshold": threshold}
            ).fetchall()
