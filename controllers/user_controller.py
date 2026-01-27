# controllers/user_controller.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.student_model import StudentModel
from utils.email_service import send_alert_email
from utils.email_service import send_otp_email
from utils.validators import validate_roll, validate_password



import time,random


user = Blueprint("user", __name__)

# -------------------------------------
# USER LOGIN
# -------------------------------------
@user.route("/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        roll = request.form.get("roll", "").strip()
        password = request.form.get("password", "").strip()

        # -------------------------
        # ROLL VALIDATION
        # -------------------------
        ok, roll_or_msg = validate_roll(roll)
        if not ok:
            flash(roll_or_msg, "error")
            return redirect(url_for("user.user_login"))
        roll = roll_or_msg

        # -------------------------
        # PASSWORD VALIDATION
        # -------------------------
        ok, pwd_or_msg = validate_password(password)
        if not ok:
            flash(pwd_or_msg, "error")
            return redirect(url_for("user.user_login"))
        password = pwd_or_msg

        # -------------------------
        # EXISTING LOGIN LOGIC
        # -------------------------
        student = StudentModel.get_by_roll(roll)

        if student and student.password == password:
            session["user_logged_in"] = True
            session["user_name"] = student.name
            session["user_roll"] = student.roll

            # Existing alert logic
            alerts, email = StudentModel.get_alerts(student.roll)
            if alerts and not session.get("alert_email_sent"):
                try:
                    send_alert_email(email, alerts)
                    session["alert_email_sent"] = True
                    flash("⚠️ Important academic alerts have been sent to your email.", "warning")
                except Exception as e:
                    print("Auto alert email failed:", e)

            flash(f"Login successful! Welcome back {student.name}", "success")
            return redirect(url_for("main.home"))

        else:
            flash("Invalid roll number or password.", "error")

    return render_template("user/user_login.html")


# -------------------------------------
# USER REGISTRATION 
# -------------------------------------

@user.route("/register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        roll = request.form.get("roll", "").strip()
        name = request.form.get("name")
        dept = request.form.get("department")
        year = request.form.get("year")
        email = request.form.get("email")
        password = request.form.get("password")

        # -------------------------
        # BASIC REQUIRED CHECK
        # -------------------------
        if not all([roll, name, email, password]):
            flash("All fields are required", "error")
            return redirect(url_for("user.user_register"))

        # -------------------------
        # ROLL VALIDATION
        # -------------------------
        ok, roll_or_msg = validate_roll(roll)
        if not ok:
            flash(roll_or_msg, "error")
            return redirect(url_for("user.user_register"))
        roll = roll_or_msg

        # -------------------------
        # PASSWORD VALIDATION
        # -------------------------
        ok, pwd_or_msg = validate_password(password)
        if not ok:
            flash(pwd_or_msg, "error")
            return redirect(url_for("user.user_register"))
        password = pwd_or_msg

        # -------------------------
        # DUPLICATE CHECKS (UNCHANGED)
        # -------------------------
        if StudentModel.get_by_roll(roll):
            flash("Roll number already registered", "error")
            return redirect(url_for("user.user_register"))

        if StudentModel.get_by_email(email):
            flash("Email already registered", "error")
            return redirect(url_for("user.user_register"))

        # -------------------------
        # OTP GENERATION
        # -------------------------
        otp = random.randint(100000, 999999)

        session["reg_data"] = {
            "roll": roll,
            "name": name,
            "department": dept,
            "year": year,
            "email": email,
            "password": password
        }
        session["reg_otp"] = str(otp)
        session["reg_otp_time"] = time.time()

        send_otp_email(email, otp)

        flash("OTP sent to your email. Verify to complete registration.", "info")

        return redirect(url_for("otp.verify_register_otp"))
       

    return render_template("user/user_register.html")

# -------------------------------------
# USER LOGOUT
# -------------------------------------
@user.route("/logout")
def user_logout():
    session.clear()   # clears all session data including alert flags
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("main.home"))
