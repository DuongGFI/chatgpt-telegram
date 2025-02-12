# Telegram AI Chatbot

## Mô tả
Bot Telegram sử dụng OpenAI GPT để trả lời tin nhắn của người dùng, lưu giữ ngữ cảnh hội thoại và tóm tắt cuộc trò chuyện. Triển khai bằng `python-telegram-bot` và `openai`. Dữ liệu hội thoại được lưu trữ vào PostgreSQL để đảm bảo ngữ cảnh không bị mất khi bot khởi động lại.

## Yêu cầu
- Python 3.8+
- API Key của OpenAI
- Token Bot Telegram
- PostgreSQL để lưu trữ dữ liệu

## Cài đặt
1. Clone repository:
   ```sh
   git clone https://github.com/DuongGFI/chatgpt-telegram.git
   cd chatgpt-telegram
   ```
2. Cài đặt các thư viện cần thiết:
   ```sh
   pip install -r requirements.txt
   ```
3. Thiết lập biến môi trường:
   - Tạo file `.env` dựa trên `.env.example` và điền thông tin cần thiết.
   - Hoặc xuất biến môi trường theo cách thủ công:
     ```sh
     export TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
     export OPENAI_API_KEY="your-openai-api-key"
     export DATABASE_URL="postgres://user:password@host:port/dbname"
     ```

## Thiết lập cơ sở dữ liệu trên Render.com
1. **Tạo PostgreSQL trên Render**:
   - Truy cập [Render](https://render.com/) → **New** → **PostgreSQL**
   - Chọn gói **Free Tier**
   - Sao chép `DATABASE_URL`
2. **Thêm biến môi trường trên Render Web Service**:
   - Truy cập Web Service → **Environment Variables**
   - Thêm biến `DATABASE_URL`
3. **Khởi tạo database khi deploy**:
   - Vào **Start Command** trên Render, đặt:
     ```sh
     python -c "from bot import Base, engine; Base.metadata.create_all(engine)" && python bot.py
     ```

## Chạy Bot
```sh
python bot.py
```

## Triển khai trên Render.com
1. Đăng ký tài khoản tại [Render](https://render.com/).
2. Tạo **New Web Service** và kết nối với GitHub repository.
3. Thiết lập biến môi trường trong **Environment Variables**.
4. Chạy bot bằng lệnh `python bot.py`.

Bot sẽ tự ping chính nó để tránh bị sleep.

## Giữ Bot Luôn Online
- Sử dụng Flask để tạo một endpoint `/` và ping nó mỗi 10 phút.
- Cài đặt UptimeRobot hoặc cron job để gửi request liên tục.
