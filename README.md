### README.md
# Telegram AI Chatbot

## Mô tả
Bot Telegram sử dụng OpenAI GPT để trả lời tin nhắn của người dùng, lưu giữ ngữ cảnh hội thoại và tóm tắt cuộc trò chuyện. Triển khai bằng `python-telegram-bot` và `openai`. Dữ liệu hội thoại được lưu trữ vào SQLite để đảm bảo ngữ cảnh không bị mất khi bot khởi động lại.

## Yêu cầu
- Python 3.8+
- API Key của OpenAI
- Token Bot Telegram
- SQLite hoặc PostgreSQL để lưu trữ dữ liệu

## Cài đặt
1. Clone repository:
   ```sh
   git clone https://github.com/yourusername/telegram-ai-bot.git
   cd telegram-ai-bot
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
     export DATABASE_URL="sqlite:///chat_history.db"
     ```

## Thiết lập cơ sở dữ liệu
1. Chạy lệnh sau để khởi tạo database:
   ```sh
   python init_db.py
   ```
2. Kiểm tra xem file `chat_history.db` đã được tạo trong thư mục dự án chưa.

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
