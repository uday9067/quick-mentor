import requests
import os

MODEL_NAME = os.getenv("LOCAL_LLM_MODEL", "phi")

def ask_local_llm(prompt):
    payload = {
        "model": MODEL_NAME,
        "prompt": f"""
You are a helpful student assistant.
Answer clearly and completely.
User: {prompt}
Assistant:
""",
        "stream": False,
        "options": {
            "temperature": 0.6,
            "top_p": 0.9,
            "num_ctx": 512,
            "num_predict": 512
        }
    }

    try:
        r = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json=payload,
            timeout=60
        )
        r.raise_for_status()
        return r.json().get("response", "").strip()
    except Exception as e:
        print("LOCAL LLM ERROR:", e)
        return "🤖 AI service is temporarily unavailable. Please try again later."
