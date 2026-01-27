# utils/decorators.py

from functools import wraps
from flask import session, redirect, url_for, flash

def user_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("user_logged_in"):
            flash("Please login first.", "error")
            return redirect(url_for("user.user_login"))   
        return func(*args, **kwargs)
    return wrapper


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Admin login required.", "error")
            return redirect(url_for("admin.admin_login"))  
        return func(*args, **kwargs)
    return wrapper
