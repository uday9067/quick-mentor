from sqlalchemy import text
from utils.db import engine
from utils.ai_client import client
from utils.email_service import send_alert_email


def get_system_status():
    status = {}

    # -------------------------
    # DATABASE STATUS (SQLAlchemy Engine)
    # -------------------------
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status["database"] = "UP"
    except Exception:
        status["database"] = "DOWN"

    # -------------------------
    # EMAIL SERVICE STATUS
    # -------------------------
    try:
        send_alert_email
        status["email"] = "CONFIGURED"
    except Exception:
        status["email"] = "NOT CONFIGURED"

    # -------------------------
    # AI SERVICE STATUS
    # -------------------------
    try:
        _ = client
        status["ai"] = "AVAILABLE"
    except Exception:
        status["ai"] = "UNAVAILABLE"

    return status
