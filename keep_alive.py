from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
from threading import Thread
import requests
import time
import os

web_app = FastAPI()

@web_app.get("/")
async def home():
    return "Bot is alive!"

@web_app.get("/health")
async def health_check():
    return JSONResponse({
        "status": "healthy",
        "timestamp": time.time(),
        "uptime": "active"
    })

def run():
    uvicorn.run(web_app, host='0.0.0.0', port=int(os.getenv('PORT', 10000)))

def keep_alive():
    server_thread = Thread(target=run)
    server_thread.daemon = True  # Để thread tự đóng khi chương trình chính kết thúc
    server_thread.start()

def ping_self():
    while True:
        try:
            url = os.getenv('RENDER_URL', 'http://localhost:10000')
            requests.get(f"{url}/health")
        except Exception as e:
            print(f"Ping failed: {str(e)}")
        time.sleep(300)  # Ping mỗi 5 phút

def start_ping():
    ping_thread = Thread(target=ping_self)
    ping_thread.daemon = True
    ping_thread.start()
