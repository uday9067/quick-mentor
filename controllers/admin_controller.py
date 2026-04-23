# controllers/admin_controller.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from utils.decorators import admin_required
from config import ADMIN_USER, ADMIN_PASS
from models.student_model import StudentModel
from models.fee_model import FeeModel
from models.timetable_model import TimetableModel
from models.chat_history_model import ChatHistoryModel
from models.system_status import get_system_status
from utils.pdf_reports import pending_fees_pdf, low_attendance_pdf
from flask import send_file
import tempfile
from datetime import datetime


import csv
from io import TextIOWrapper


admin = Blueprint("admin", __name__, url_prefix="/admin")

# ------------------------------
# Admin Login
# ------------------------------
@admin.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == ADMIN_USER and password == ADMIN_PASS:
            session["is_admin"] = True
            flash("Logged in successfully!", "success")
            return redirect(url_for("admin.admin_dashboard"))
        else:
            flash("Invalid admin credentials.", "error")

    return render_template("admin/admin_login.html")


# ------------------------------
# Admin Dashboard
# ------------------------------
@admin.route("/")
@admin_required
def admin_dashboard():

    stats = {
        "students": StudentModel.count(),
        "fees": FeeModel.count(),
        "timetable": TimetableModel.count()
    }

    low_attendance_students = StudentModel.get_low_attendance_students()
    pending_fee_students = FeeModel.get_pending_fee_students()

    # fetch current system status and pass to dashboard template
    status = get_system_status()

    return render_template(
        "admin/admin_dashboard.html",
        stats=stats,
        low_attendance_students=low_attendance_students,
        pending_fee_students=pending_fee_students,
        system_status=status
    )



# ------------------------------
# Manage Students
# ------------------------------
@admin.route("/students")
@admin_required
def admin_students():
    students = StudentModel.get_all()
    return render_template("admin/admin_students.html", students=students)


# Add a new student
@admin.route("/students/add", methods=["POST"])
@admin_required
def admin_students_add():

    roll = request.form.get("roll", "").strip()
    email = request.form.get("email")

    # -------------------------------
    # ROLL NUMBER VALIDATION (25xxx)
    # -------------------------------
    if not (roll.isdigit() and roll.startswith("25") and len(roll) >= 5):
        flash(
            "❌ Invalid roll number! Roll number must start with 25xxx (e.g. 25001).",
            "error"
        )
        return redirect(url_for("admin.admin_students"))

    # -------------------------------
    # EMAIL DUPLICATE CHECK
    # -------------------------------
    if StudentModel.get_by_email(email):
        flash(
            "⚠️ This email is already registered with another student.",
            "error"
        )
        return redirect(url_for("admin.admin_students"))

    # -------------------------------
    # CREATE STUDENT
    # -------------------------------
    success = StudentModel.create(
        roll=roll,
        name=request.form.get("name"),
        department=request.form.get("department"),
        year=request.form.get("year"),
        email=email,
        password="1234",
        attendance=request.form.get("attendance")
    )

    # -------------------------------
    # ROLL DUPLICATE CHECK (MODEL LEVEL)
    # -------------------------------
    if not success:
        flash(
            "⚠️ Roll number already exists. Please verify the roll number before adding the student.",
            "error"
        )
        return redirect(url_for("admin.admin_students"))

    flash("✅ Student added successfully!", "success")
    return redirect(url_for("admin.admin_students"))


# Edit the student
@admin.route("/students/update/<int:sid>", methods=["POST"])
@admin_required
def admin_students_update(sid):

    email = request.form.get("email")

    # -------------------------------
    # EMAIL DUPLICATE CHECK (UPDATE)
    # -------------------------------
    existing = StudentModel.get_by_email(email)
    if existing and existing.id != sid:
        flash(
            "⚠️ This email is already assigned to another student.",
            "error"
        )
        return redirect(url_for("admin.admin_students"))

    StudentModel.update_admin(
        sid=sid,
        name=request.form.get("name"),
        department=request.form.get("department"),
        year=request.form.get("year"),
        attendance=request.form.get("attendance"),
        email=email
    )

    flash("Student updated successfully!", "success")
    return redirect(url_for("admin.admin_students"))

# admin fee update

@admin.route("/fees/update/<int:fid>", methods=["POST"])
@admin_required
def admin_fees_update(fid):
    FeeModel.update(
        fid=fid,
        semester=request.form.get("semester"),
        amount_due=request.form.get("amount_due"),
        amount_paid=request.form.get("amount_paid"),
        due_date=request.form.get("due_date"),
    )

    flash("Fee record updated successfully!", "success")
    return redirect(url_for("admin.admin_fees"))


@admin.route("/students/delete/<int:sid>", methods=["POST"])
@admin_required
def admin_students_delete(sid):
    StudentModel.delete(sid)
    flash("Student deleted!", "info")
    return redirect(url_for("admin.admin_students"))


# -----------------------------------
# Manage Fees
# -----------------------------------
@admin.route("/fees")
@admin_required
def admin_fees():
    fees = FeeModel.get_all()
    return render_template("admin/admin_fees.html", fees=fees)


@admin.route("/admin/fees/add", methods=["POST"])
@admin_required
def admin_fees_add():

    roll = request.form.get("roll")
    semester = int(request.form.get("semester") or 1)

    # 🔴 Prevent duplicate fee entry
    if FeeModel.exists_for_roll_semester(roll, semester):
        flash(
            f"⚠️ Fee record already exists for Roll {roll}, Semester {semester}.",
            "error"
        )
        return redirect(url_for("admin.admin_fees"))

    FeeModel.create(
        roll=roll,
        semester=semester,
        amount_due=request.form.get("amount_due"),
        amount_paid=request.form.get("amount_paid"),
        due_date=request.form.get("due_date")
    )

    flash("✅ Fee record added successfully!", "success")
    return redirect(url_for("admin.admin_fees"))


@admin.route("/fees/delete/<int:fid>", methods=["POST"])
@admin_required
def admin_fees_delete(fid):
    FeeModel.delete(fid)
    flash("Fee record deleted!", "info")
    return redirect(url_for("admin.admin_fees"))


# -----------------------------------
# Manage Timetable
# -----------------------------------
@admin.route("/timetable")
@admin_required
def admin_timetable():
    rows = TimetableModel.get_all()
    return render_template("admin/admin_timetable.html", timetable=rows)


# Admin Timetable add
@admin.route("/timetable/add", methods=["POST"])
@admin_required
def admin_timetable_add():

    class_date = request.form.get("class_date")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")

    # 🔴 Time clash check
    if TimetableModel.has_time_clash(class_date, start_time, end_time):
        flash(
            "⚠️ Time clash detected! Another class already exists during this time.",
            "error"
        )
        return redirect(url_for("admin.admin_timetable"))

    TimetableModel.create(
        day=request.form.get("day"),
        class_date=class_date,
        start_time=start_time,
        end_time=end_time,
        subject=request.form.get("subject"),
        instructor=request.form.get("instructor"),
        location=request.form.get("location"),
    )

    flash("Timetable entry added successfully!", "success")
    return redirect(url_for("admin.admin_timetable"))


@admin.route("/timetable/upload", methods=["POST"])
@admin_required
def admin_timetable_upload():
    file = request.files.get("file")

    if not file:
        flash("No file uploaded.", "error")
        return redirect(url_for("admin.admin_timetable"))

    import csv
    from io import TextIOWrapper

    try:
        reader = csv.DictReader(TextIOWrapper(file.stream, encoding="utf-8"))

        for row in reader:
            TimetableModel.create(
                day=row.get("day"),
                start_time=row.get("start_time"),
                end_time=row.get("end_time"),
                subject=row.get("subject"),
                instructor=row.get("instructor"),
                location=row.get("location"),
            )

        flash("CSV uploaded successfully!", "success")

    except Exception as e:
        print("UPLOAD ERROR:", e)
        flash("Error while processing file.", "error")

    return redirect(url_for("admin.admin_timetable"))

@admin.route("/timetable/delete/<int:tid>", methods=["POST"])
@admin_required
def admin_timetable_delete(tid):
    TimetableModel.delete(tid)
    flash("Timetable entry removed successfully!", "info")
    return redirect(url_for("admin.admin_timetable"))


@admin.route("/timetable/edit/<int:tid>")
@admin_required
def admin_timetable_edit(tid):
    timetable = TimetableModel.get_by_id(tid)
    return render_template(
        "admin/admin_timetable_edit.html",
        t=timetable
    )


# Admin Timetable Update
@admin.route("/timetable/update/<int:tid>", methods=["POST"])
@admin_required
def admin_timetable_update(tid):

    day = request.form.get("day")
    class_date = request.form.get("class_date")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")
    subject = request.form.get("subject")
    instructor = request.form.get("instructor")
    location = request.form.get("location")

    # 🔴 Required field validation
    if not all([day, class_date, start_time, end_time, subject]):
        flash("⚠️ Day, date, start time, end time and subject are required.", "error")
        return redirect(url_for("admin.admin_timetable"))

    # 🧠 Fetch old row (to detect real time changes)
    old = TimetableModel.get_by_id(tid)

    # 🔴 Run clash check ONLY if time/day/date changed
    if (
        old.class_date != class_date
        or old.day != day
        or old.start_time != start_time
        or old.end_time != end_time
    ):
        if TimetableModel.has_time_clash(
            class_date=class_date,
            day=day,
            start_time=start_time,
            end_time=end_time,
            exclude_id=tid
        ):
            flash(
                "⚠️ Time clash detected! Another class already exists during this time.",
                "error"
            )
            return redirect(url_for("admin.admin_timetable"))

    # ✅ Update allowed
    TimetableModel.update(
        tid=tid,
        day=day,
        class_date=class_date,
        start_time=start_time,
        end_time=end_time,
        subject=subject,
        instructor=instructor,
        location=location,
    )

    flash("✅ Timetable updated successfully!", "success")
    return redirect(url_for("admin.admin_timetable"))

# Admin Logs
# -----------------------------------

@admin.route("/chat-logs")
@admin_required
def chat_logs():
    logs = ChatHistoryModel.get_recent()
    return render_template("admin/chat_logs.html", logs=logs)


@admin.route("/system-status")
@admin_required
def system_status():
    status = get_system_status()
    return render_template("admin/system_status.html", status=status)

# -----------------------------------
# Admin Logout
# -----------------------------------
@admin.route("/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("Admin logged out!", "success")
    return redirect(url_for("admin.admin_login"))


# -----------------------------------
# Upload Students CSV
# -----------------------------------
@admin.route("/students/upload", methods=["POST"])
@admin_required
def admin_students_upload():

    file = request.files.get("file")

    if not file:
        flash("No file uploaded.", "error")
        return redirect(url_for("admin.admin_students"))

    import csv
    from io import TextIOWrapper

    skipped = 0
    added = 0

    try:
        # ✅ Handle BOM (Excel safe)
        text_file = TextIOWrapper(file.stream, encoding="utf-8-sig")

        # ✅ Detect delimiter (, or ;)
        sample = text_file.read(1024)
        text_file.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=",;")

        reader = csv.DictReader(text_file, dialect=dialect)

        # ✅ Normalize headers (case + spaces)
        reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]

        for row in reader:
            # ✅ Normalize roll value
            roll = str(row.get("roll", "")).strip()

            # 🔴 Roll validation (25xxx)
            if not is_valid_roll(roll):
                skipped += 1
                continue

            # 🔴 Skip duplicate roll
            if StudentModel.get_by_roll(roll):
                skipped += 1
                continue

            StudentModel.create(
                roll=roll,
                name=(row.get("name") or "").strip(),
                department=(row.get("department") or "").strip(),
                year=row.get("year"),
                email=(row.get("email") or "").strip(),
                password="1234",
                attendance=row.get("attendance") or 0
            )

            added += 1

        flash(
            f"✅ Upload completed: {added} added, {skipped} skipped (invalid/duplicate rolls)",
            "success"
        )

    except Exception as e:
        print("STUDENT CSV UPLOAD ERROR:", e)
        flash("❌ Error while processing CSV file.", "error")

    return redirect(url_for("admin.admin_students"))


def is_valid_roll(roll):
    """
    Valid roll number:
    - Must be numeric
    - Must start with '25'
    - Minimum length: 5 (e.g. 25001)
    """
    if not roll:
        return False

    roll = roll.strip()

    return roll.isdigit() and roll.startswith("25") and len(roll) >= 5


# -----------------------------------
# Upload Fees CSV
# -----------------------------------
@admin.route("/admin/fees/upload", methods=["POST"])
@admin_required
def admin_fees_upload():

    file = request.files.get("file")

    if not file:
        flash("No file uploaded.", "error")
        return redirect(url_for("admin.admin_fees"))

    import csv
    from io import TextIOWrapper

    skipped = 0
    added = 0

    try:
        # ✅ Handle Excel BOM
        text_file = TextIOWrapper(file.stream, encoding="utf-8-sig")

        # ✅ Auto-detect delimiter
        sample = text_file.read(1024)
        text_file.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=",;")

        reader = csv.DictReader(text_file, dialect=dialect)
        reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]

        for row in reader:
            roll = str(row.get("roll", "")).strip()
            semester = int(row.get("semester") or 1)

            # 🔴 Roll validation (25xxx)
            if not (roll.isdigit() and roll.startswith("25")):
                skipped += 1
                continue

            # 🔴 Student must exist
            if not StudentModel.get_by_roll(roll):
                skipped += 1
                continue

            # 🔴 Prevent duplicate fee (roll + semester)
            if FeeModel.exists_for_roll_semester(roll, semester):
                skipped += 1
                continue

            FeeModel.create(
                roll=roll,
                semester=semester,
                amount_due=row.get("amount_due") or 0,
                amount_paid=row.get("amount_paid") or 0,
                due_date=parse_csv_date(row.get("due_date"))
            )

            added += 1

        flash(
            f"✅ Fees upload completed: {added} added, {skipped} skipped",
            "success"
        )

    except Exception as e:
        print("FEES CSV UPLOAD ERROR:", e)
        flash("❌ Error while processing fees CSV.", "error")

    return redirect(url_for("admin.admin_fees"))

# Download Pending Fees PDF

@admin.route("/admin/reports/pending-fees")
@admin_required
def download_pending_fees_pdf():

    data = FeeModel.get_pending_fee_students()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pending_fees_pdf(data, tmp.name)

    return send_file(
        tmp.name,
        as_attachment=True,
        download_name="pending_fees_report.pdf"
    )

@admin.route("/admin/reports/low-attendance")
@admin_required
def download_low_attendance_pdf():

    data = StudentModel.get_low_attendance_students()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    low_attendance_pdf(data, tmp.name)

    return send_file(
        tmp.name,
        as_attachment=True,
        download_name="low_attendance_report.pdf"
    )
    


def parse_csv_date(date_str):
    """
    Converts CSV date (DD-MM-YYYY) to MySQL DATE (YYYY-MM-DD)
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%d-%m-%Y").date()
    except ValueError:
        return None
# -----------------------------------
# Admin Chart Data APIs
# -----------------------------------

@admin.route("/api/charts/attendance")
@admin_required
def api_chart_attendance():
    """
    Returns data for attendance distribution chart
    """
    students = StudentModel.get_all()
    
    # Categorize students by attendance ranges
    ranges = {
        "Above 90%": 0,
        "75% - 90%": 0,
        "60% - 75%": 0,
        "Below 60%": 0
    }
    
    for s in students:
        att = float(s.attendance or 0)
        if att >= 90:
            ranges["Above 90%"] += 1
        elif att >= 75:
            ranges["75% - 90%"] += 1
        elif att >= 60:
            ranges["60% - 75%"] += 1
        else:
            ranges["Below 60%"] += 1
            
    return jsonify({
        "labels": list(ranges.keys()),
        "data": list(ranges.values())
    })


@admin.route("/api/charts/fees")
@admin_required
def api_chart_fees():
    """
    Returns data for fee status chart (Paid vs Pending)
    """
    fees = FeeModel.get_all()
    
    total_due = 0
    total_paid = 0
    
    for f in fees:
        total_due += float(f.amount_due or 0)
        total_paid += float(f.amount_paid or 0)
        
    pending = total_due - total_paid
    
    return jsonify({
        "labels": ["Paid Amount", "Pending Amount"],
        "data": [total_paid, pending if pending > 0 else 0]
    })


@admin.route("/api/charts/chats")
@admin_required
def api_chart_chats():
    """
    Returns data for chat activity (Intent distribution)
    """
    logs = ChatHistoryModel.get_recent(limit=500)
    
    intents = {}
    for log in logs:
        # Clean up intent name for labels
        intent = log.intent.replace("_", " ").title()
        intents[intent] = intents.get(intent, 0) + 1
        
    # Sort and get top 5
    sorted_intents = sorted(intents.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return jsonify({
        "labels": [x[0] for x in sorted_intents],
        "data": [x[1] for x in sorted_intents]
    })
