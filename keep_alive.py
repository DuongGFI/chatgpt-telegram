from flask import Flask
from threading import Thread
import requests
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_awake():
    while True:
        try:
            url = os.getenv("RENDER_URL")  # Lấy URL từ biến môi trường
            if url:
                requests.get(url, timeout=5)
            time.sleep(600)  # Ping mỗi 10 phút
        except Exception as e:
            print(f"Ping failed: {e}")

# Chạy Flask server và self-ping cùng lúc
def start_keep_alive():
    t1 = Thread(target=run)
    t2 = Thread(target=keep_awake)
    t1.start()
    t2.start()
