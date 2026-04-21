from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)

# app.py
from flask import Flask
from config import SECRET_KEY, GOOGLE_API_KEY, MODEL_NAME
from google import genai
from utils.ai_client import client, MODEL

import threading
from utils.local_llm import ask_local_llm


# Create Flask app FIRST
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Session config (browser-session only)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True



def warm_up_llm():
    try:
        ask_local_llm("hello")
        print("✅The System is Good to Goo!!")
    except Exception as e:
        print("LLM warm-up failed:", e)

threading.Thread(target=warm_up_llm).start()



# --- Initialize GenAI ---
from google import genai
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY


# --- Register DB ---
from utils.db import engine


# --- Register Controllers (BLUEPRINTS) ---
# ⭐ MUST come AFTER app = Flask(...)
from controllers.main_controller import main
from controllers.user_controller import user
from controllers.admin_controller import admin
from controllers.chat_controller import chat
from controllers.otp_controller import otp    
from controllers.profile_controller import profile

app.register_blueprint(main)
app.register_blueprint(user)
app.register_blueprint(admin)
app.register_blueprint(chat)
app.register_blueprint(otp)
app.register_blueprint(profile)




# No-cache for admin pages
@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response


if __name__ == "__main__":
    # app.run(debug=True)     localhost only
    app.run( host="0.0.0.0",    
             port=5000,
             debug=True)       
