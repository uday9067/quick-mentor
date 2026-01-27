# controllers/otp_controller.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.email_service import send_otp_email
from models.student_model import StudentModel
from models.fee_model import FeeModel
import random
import time


otp = Blueprint("otp", __name__)

# ------------------------------
# 1. Forgot Password → Enter Email
# ------------------------------

@otp.route("/forgot", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")

        user = StudentModel.get_by_email(email)
        if not user:
            flash("Email not found!", "error")
            return redirect(url_for("otp.forgot_password"))

        # Generate OTP
        generated_otp = random.randint(100000, 999999)

        # Save in session
        session["reset_email"] = email
        session["reset_otp"] = str(generated_otp)
        session["reset_otp_time"] = time.time()


        # Send OTP to email
        send_otp_email(email, generated_otp)

        flash("OTP sent to your email!", "success")
        return redirect(url_for("otp.verify_otp"))

    return render_template("otp/forgot.html")


# ------------------------------
# 2. Verify OTP Page
# ------------------------------
@otp.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        entered_otp = request.form.get("otp")

        entered_otp = request.form.get("otp")

        # 🔴 SAFETY CHECK
        if "reset_otp" not in session or "reset_otp_time" not in session:
            flash("OTP expired. Please resend OTP.", "error")
            return redirect(url_for("otp.resend_otp"))

        # ⏳ EXPIRY CHECK
        if time.time() - session["reset_otp_time"] > 300:
            flash("OTP expired. Please resend OTP.", "error")
            return redirect(url_for("otp.resend_otp"))

        # ✅ OTP MATCH CHECK
        if entered_otp == session["reset_otp"]:
            flash("OTP verified! Set a new password.", "success")
            return redirect(url_for("otp.reset_password"))
        else:
            flash("Invalid OTP!", "error")


    return render_template("otp/verify_otp.html")


# ------------------------------
# 3. Reset Password
# ------------------------------
@otp.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        new_pass = request.form.get("password")
        email = session.get("reset_email")

        if not email:
            flash("Session expired! Try again.", "error")
            return redirect(url_for("otp.forgot_password"))

        # Update user password
        StudentModel.update_password(email, new_pass)

        # Clear session reset data
        session.pop("reset_email", None)
        session.pop("reset_otp", None)

        flash("Password updated successfully! Please login.", "success")
        return redirect(url_for("user.user_login"))  # FIXED

    return render_template("otp/reset_password.html")


# controllers/otp_controller.py

from models.student_model import StudentModel

@otp.route("/verify_register_otp", methods=["GET", "POST"])
def verify_register_otp():

    # ❗ Direct access protection
    if "reg_otp" not in session:
        flash("Session expired. Please register again.", "error")
        return redirect(url_for("user.user_register"))

    if request.method == "POST":
        entered_otp = request.form.get("otp", "").strip()


        if time.time() - session.get("reg_otp_time", 0) > 300:
            flash("OTP expired. Please resend OTP.", "error")
            return redirect(url_for("otp.resend_otp"))

        
        if entered_otp != session.get("reg_otp"):
            flash("Invalid OTP!", "error")
            return redirect(url_for("otp.verify_register_otp"))


        data = session.get("reg_data")
        roll = data["roll"]

        # ✅ Create student only AFTER OTP verification
        StudentModel.create(
            roll=data["roll"],
            name=data["name"],
            department=data["department"],
            year=data["year"],
            email=data["email"],
            password=data["password"]
        )
        # -------------------------------
        # CREATE DEFAULT FEE RECORD
        # -------------------------------
        FeeModel.create(
            roll=roll,
            semester=1,
            amount_due=0,
            amount_paid=0,
            due_date=None
        )


        # 🧹 Cleanup
        session.pop("reg_data", None)
        session.pop("reg_otp", None)
        session.pop("reg_otp_time", None)

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("user.user_login"))

    return render_template("otp/verify_register_otp.html")


# ------------------------------
# RESEND OTP (COMMON)
# ------------------------------
@otp.route("/resend_otp")
def resend_otp():

    # Registration OTP
    if "reg_data" in session:
        email = session["reg_data"]["email"]

        new_otp = random.randint(100000, 999999)
        session["reg_otp"] = str(new_otp)
        session["reset_otp_time"] = time.time() 

        send_otp_email(email, new_otp)
        flash("OTP resent to your email.", "success")
        return redirect(url_for("otp.verify_register_otp"))

    # Forgot-password OTP
    if "reset_email" in session:
        email = session["reset_email"]

        new_otp = random.randint(100000, 999999)
        session["reset_otp"] = str(new_otp)
        session["reset_otp_time"] = time.time() 

        send_otp_email(email, new_otp)
        flash("OTP resent to your email.", "success")
        return redirect(url_for("otp.verify_otp"))

    flash("Session expired. Please try again.", "error")
    return redirect(url_for("user.user_login"))
