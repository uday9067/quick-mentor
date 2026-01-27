# controllers/main_controller.py

from flask import Blueprint, render_template, redirect, url_for, session, flash
from utils.decorators import user_required

main = Blueprint("main", __name__)

# -------------------------------
# Home Page
# -------------------------------
@main.route("/")
def home():
    return render_template("home.html")

# -------------------------------
# User Logout (Student logout)
# -------------------------------
@main.route("/logout")
def logout():
    session.clear()
    flash("Logout successful!", "success")
    return redirect(url_for("main.home"))

# -------------------------------
# Chat Page (Protected)
# -------------------------------
@main.route("/chat")
@user_required
def chat_page():
    return render_template("chat.html")
