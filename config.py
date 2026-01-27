# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# ---------- DB CONFIG ----------
DB_USER = os.getenv("DATABASE_USER")
DB_PASS = os.getenv("DATABASE_PASS")
DB_HOST = os.getenv("DATABASE_HOST", "localhost")
DB_PORT = os.getenv("DATABASE_PORT", "3306")
DB_NAME = os.getenv("DATABASE_NAME")

if not all([DB_USER, DB_PASS, DB_NAME]):
    raise Exception("Missing database credentials in .env")

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ---------- ADMIN CONFIG ----------
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")

# ---------- AI CONFIG ----------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyANwPoPH7I1ABFiIBf5tAzusJJGxbV24SE")
MODEL_NAME = "models/gemini-2.0-flash"

# ---------- FLASK SECRET ----------
SECRET_KEY = os.getenv("SECRET_KEY", "ChatBot_Secrete_Key")

# ---------- EMAIL / OTP CONFIG (OPTIONAL) ----------
EMAIL_USER = os.getenv("EMAIL_USER", "your@gmail.com")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "your-google-app-password")
