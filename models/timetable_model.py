# models/timetable_model.py
from utils.db import engine
from sqlalchemy import text
from datetime import datetime


class TimetableModel:

    # -------------------------
    # GET ALL
    # -------------------------
    @staticmethod
    def get_all():
        with engine.connect() as conn:
            q = text("""
                SELECT * FROM timetable
                ORDER BY class_date, start_time
            """)
            return conn.execute(q).fetchall()


    # -------------------------
    # CREATE (SAFE + BACKWARD COMPATIBLE)
    # -------------------------
    @staticmethod
    def create(day, class_date=None, start_time=None, end_time=None,
               subject=None, instructor=None, location=None):

        # 🔒 Auto-fill date if missing (prevents crash)
        if not class_date:
            class_date = datetime.now().date()

        with engine.connect() as conn:
            q = text("""
                INSERT INTO timetable 
                (day, class_date, start_time, end_time, subject, instructor, location)
                VALUES (:day, :class_date, :start_time, :end_time, :subject, :instructor, :location)
            """)
            conn.execute(q, {
                "day": day,
                "class_date": class_date,
                "start_time": start_time,
                "end_time": end_time,
                "subject": subject,
                "instructor": instructor,
                "location": location
            })
            conn.commit()


    # -------------------------
    # TIME CLASH CHECK
    # -------------------------
    @staticmethod
    def has_time_clash(class_date, day, start_time, end_time, exclude_id=None):
        with engine.connect() as conn:
            query = """
                SELECT COUNT(*) FROM timetable
                WHERE class_date = :class_date
                AND day = :day
                AND start_time < :end_time
                AND end_time > :start_time
            """

            params = {
                "class_date": class_date,
                "day": day,
                "start_time": start_time,
                "end_time": end_time
            }

            if exclude_id:
                query += " AND id != :id"
                params["id"] = exclude_id

            return conn.execute(text(query), params).scalar() > 0


    # -------------------------
    # DELETE
    # -------------------------
    @staticmethod
    def delete(tid):
        with engine.connect() as conn:
            conn.execute(
                text("DELETE FROM timetable WHERE id = :id"),
                {"id": tid}
            )
            conn.commit()


    # -------------------------
    # UPDATE
    # -------------------------
    @staticmethod
    def update(tid, day, class_date, start_time, end_time,
               subject, instructor, location):

        with engine.connect() as conn:
            q = text("""
                UPDATE timetable
                SET day = :day,
                    class_date = :class_date,
                    start_time = :start_time,
                    end_time = :end_time,
                    subject = :subject,
                    instructor = :instructor,
                    location = :location
                WHERE id = :id
            """)
            conn.execute(q, {
                "id": tid,
                "day": day,
                "class_date": class_date,
                "start_time": start_time,
                "end_time": end_time,
                "subject": subject,
                "instructor": instructor,
                "location": location
            })
            conn.commit()


    # -------------------------
    # COUNT
    # -------------------------
    @staticmethod
    def count():
        with engine.connect() as conn:
            return conn.execute(
                text("SELECT COUNT(*) FROM timetable")
            ).scalar()


    # -------------------------
    # GET BY ID
    # -------------------------
    @staticmethod
    def get_by_id(tid):
        with engine.connect() as conn:
            return conn.execute(
                text("SELECT * FROM timetable WHERE id = :id"),
                {"id": tid}
            ).fetchone()


    # -------------------------
    # TODAY'S CLASSES
    # -------------------------
    @staticmethod
    def get_today_classes():
        today = datetime.now().strftime("%A")

        with engine.connect() as conn:
            return conn.execute(
                text("""
                    SELECT subject, start_time, end_time, instructor, location
                    FROM timetable
                    WHERE day = :day
                    ORDER BY start_time
                """),
                {"day": today}
            ).fetchall()


    # -------------------------
    # NEXT CLASS
    # -------------------------
    @staticmethod
    def get_next_class():
        today = datetime.now().strftime("%A")
        now = datetime.now().strftime("%H:%M")

        with engine.connect() as conn:
            return conn.execute(
                text("""
                    SELECT subject, start_time, end_time, instructor, location
                    FROM timetable
                    WHERE day = :day
                    AND start_time > :now
                    ORDER BY start_time
                    LIMIT 1
                """),
                {"day": today, "now": now}
            ).fetchone()
