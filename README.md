# ChatGPT Telegram Bot

Đây là dự án bot Telegram tích hợp ChatGPT, sử dụng FastAPI để xử lý webhook, lưu trữ lịch sử trò chuyện với SQLAlchemy và giữ server luôn bật qua cơ chế self-ping khi triển khai trên Render.com.

## Tính năng

- **Tương tác với Telegram:** Nhận và xử lý tin nhắn của người dùng qua webhook.
- **ChatGPT Integration:** Sử dụng OpenAI API để tạo phản hồi thông minh từ ChatGPT.
- **Lưu trữ lịch sử trò chuyện:** Ghi nhận và lưu trữ lịch sử trò chuyện qua SQLAlchemy.
- **Webhook với FastAPI:** Xây dựng API bằng FastAPI, cung cấp endpoint `/webhook` để nhận cập nhật từ Telegram và endpoint `/docs` để xem tài liệu API.
- **Keep Alive:** Tích hợp cơ chế tự ping (self-ping) sử dụng FastAPI để duy trì uptime khi triển khai trên Render.com.

## Yêu cầu

- Python 3.8 trở lên
- Các gói Python được liệt kê trong [requirements.txt](requirements.txt)

## Cài đặt

1. **Clone repository:**

   ```bash
   git clone https://github.com/DuongGFI/chatgpt-telegram.git
   cd chatgpt-telegram
   ```

2. **Cài đặt các gói cần thiết:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Cấu hình biến môi trường:**

   Bạn có thể tạo file `.env` hoặc thiết lập trực tiếp trong môi trường với các biến sau:
   
   - `TELEGRAM_BOT_TOKEN`: Token của bot Telegram.
   - `OPENAI_API_KEY`: API key của OpenAI.
   - `DATABASE_URL`: URL kết nối đến cơ sở dữ liệu (ví dụ: PostgreSQL).
   - `WEBHOOK_URL`: URL webhook public của ứng dụng (ví dụ: `https://your-app.onrender.com/webhook`).
   - `RENDER_URL`: URL của ứng dụng trên Render.com (ví dụ: `https://your-app.onrender.com/`).

## Cấu trúc dự án

- **bot.py:**  
  File chính chứa logic của bot, tích hợp FastAPI với endpoint `/webhook` để nhận cập nhật từ Telegram, xử lý tin nhắn, tương tác với OpenAI API và lưu trữ lịch sử trò chuyện.

- **keep_alive.py:**  
  File tích hợp FastAPI để giữ cho server luôn bật bằng cách tự động ping chính URL của ứng dụng ở mỗi 10 phút. (Xem phần [Keep Alive](#keep-alive) bên dưới.)

- **requirements.txt:**  
  Danh sách các gói cần cài đặt.

## Chạy dự án cục bộ

1. **Chạy ứng dụng FastAPI:**

   ```bash
   uvicorn bot:web_app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Kiểm tra hoạt động của server:**

   - Truy cập `http://localhost:8000/` để xác nhận server đang chạy.
   - Truy cập `http://localhost:8000/docs` để xem tài liệu API do FastAPI tạo ra.

## Keep Alive

File `keep_alive.py` đã được viết lại sử dụng FastAPI để duy trì uptime thông qua background task tự ping:

```python
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
            url = os.getenv("RENDER_URL")  # URL của ứng dụng, ví dụ: https://your-app.onrender.com/
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
```

*Lưu ý:*  
- Đảm bảo biến môi trường `RENDER_URL` được thiết lập chính xác.
- Nếu bạn sử dụng gói Always On của Render.com, cơ chế self-ping có thể không cần thiết.

## Triển khai trên Render.com

1. **Đẩy mã nguồn lên GitHub:**  
   Đảm bảo toàn bộ dự án (bao gồm `bot.py`, `keep_alive.py` và `requirements.txt`) đã được đẩy lên repository GitHub.

2. **Tạo dịch vụ Web trên Render.com:**
   - **Build Command:**  
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command:**  
     ```bash
     uvicorn bot:web_app --host 0.0.0.0 --port $PORT
     ```

3. **Thiết lập biến môi trường:**  
   Trong Render Dashboard, cấu hình các biến môi trường: `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `DATABASE_URL`, `WEBHOOK_URL` và `RENDER_URL`.

4. **Đăng ký webhook với Telegram:**  
   - Khi ứng dụng khởi động, bạn có thể tự động đăng ký webhook qua code hoặc thực hiện thủ công bằng cách truy cập URL:
     ```
     https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook?url=https://your-app.onrender.com/webhook
     ```
   - Thay `<TELEGRAM_BOT_TOKEN>` và `your-app` bằng giá trị tương ứng.

## Đóng góp

Các đóng góp cho dự án rất được hoan nghênh. Hãy mở issue hoặc pull request nếu bạn muốn báo cáo lỗi, đưa ra cải tiến hoặc thêm tính năng mới.

## Giấy phép

Dự án này được cấp phép theo [MIT License](LICENSE).
