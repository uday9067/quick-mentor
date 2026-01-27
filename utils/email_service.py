import smtplib
import os
from email.message import EmailMessage

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# for otp
def send_otp_email(to_email, otp):
    try:
        msg = EmailMessage()
        msg["Subject"] = "Student Assistant - OTP Verification"
        msg["From"] = EMAIL_USER
        msg["To"] = to_email

        msg.set_content(
            f"""
Hello 👋

Your OTP is: {otp}

This OTP is valid for 5 minutes.
Do not share it with anyone.

Regards,
-College Administration
"""
        )

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)

        print("✅ OTP sent successfully")

    except Exception as e:
        print("❌ OTP ERROR:", e)
        raise

# Acadamic email alert

def send_alert_email(to_email, alerts):

    try:
        msg = EmailMessage()
        msg["Subject"] = "Important Academic Alert"
        msg["From"] = EMAIL_USER
        msg["To"] = to_email

        body = (
            "Dear Student,\n\n"
            "Please note the following important academic alerts:\n\n"
        )

        for alert in alerts:
            body += f"- {alert}\n"

        body += "\nPlease take necessary action.\n\nRegards,\nCollege Administration"

        msg.set_content(body)

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)

        print("✅ Alert email sent successfully")

    except Exception as e:
        print("❌ ALERT EMAIL ERROR:", e)
