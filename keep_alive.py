from threading import Thread
import uvicorn
import requests
import time
import os

def run():
    # Import web_app từ bot.py
    from bot import web_app
    uvicorn.run(web_app, host='0.0.0.0', port=int(os.getenv('PORT', 10000)))

def keep_alive():
    server_thread = Thread(target=run)
    server_thread.daemon = True
    server_thread.start()

def ping_self():
    while True:
        try:
            url = os.getenv('RENDER_URL', 'http://localhost:10000')
            requests.get(f"{url}/health")
        except Exception as e:
            print(f"Ping failed: {str(e)}")
        time.sleep(300)

def start_ping():
    ping_thread = Thread(target=ping_self)
    ping_thread.daemon = True
    ping_thread.start()
