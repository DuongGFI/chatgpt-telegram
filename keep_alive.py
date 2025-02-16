from fastapi import FastAPI
import requests
import os
import time
import threading

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Bot is running!"}

def keep_awake():
    while True:
        try:
            url = os.getenv("RENDER_URL")  # URL của ứng dụng (ví dụ: https://your-app.onrender.com/)
            if url:
                response = requests.get(url, timeout=5)
                print(f"Ping response: {response.status_code}")
            time.sleep(600)  # Ping mỗi 10 phút
        except Exception as e:
            print(f"Ping failed: {e}")

@app.on_event("startup")
def start_keep_awake():
    thread = threading.Thread(target=keep_awake, daemon=True)
    thread.start()
