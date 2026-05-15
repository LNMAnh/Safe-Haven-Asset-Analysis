# test_key.py
from pathlib import Path
from dotenv import load_dotenv
import os
from groq import Groq

# Thay bằng đường dẫn tuyệt đối tới file .env của bạn
ENV_PATH = Path(__file__).resolve().parent / ".env"
print(f"Looking for .env at: {ENV_PATH}")
print(f".env exists: {ENV_PATH.exists()}")

load_dotenv(ENV_PATH)

api_key = os.getenv("GROQ_API_KEY")
print(f"Key found: {bool(api_key)}")
print(f"Key value: '{api_key}'")
print(f"Key length: {len(api_key) if api_key else 0}")

client = Groq(api_key=api_key)
resp = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Say hello"}],
    max_tokens=10,
)
print("SUCCESS:", resp.choices[0].message.content)