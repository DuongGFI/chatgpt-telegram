# ChatGPT Telegram Bot

Dự án này là một Telegram chat bot tích hợp ChatGPT, được thiết kế để duy trì ngữ cảnh trò chuyện hiệu quả qua việc lưu trữ 10 tin nhắn gần nhất và tự động tóm tắt các tin nhắn cũ hơn trước khi gửi cho ChatGPT. Đồng thời, dự án sử dụng cơ chế self-ping để giữ kết nối ổn định trên Render.com.

## Tính năng

- **Tích hợp ChatGPT:**  
  Bot sử dụng API của OpenAI để tạo ra các phản hồi thông minh, mang đến trải nghiệm trò chuyện tự nhiên cho người dùng.

- **Lưu trữ và Quản lý Ngữ cảnh:**  
  - **Lưu 10 tin nhắn gần nhất:** Dự án lưu lại 10 tin nhắn cuối cùng để duy trì thông tin ngữ cảnh cần thiết cho cuộc trò chuyện.  
  - **Tóm tắt tin nhắn cũ:** Các tin nhắn xa hơn sẽ được tóm tắt lại và gửi cho ChatGPT nhằm giữ lại ngữ cảnh tổng thể của cuộc trò chuyện mà không bị quá tải dữ liệu.

- **Cơ chế Self-Ping:**  
  Để duy trì kết nối liên tục và tránh tình trạng server bị “ngủ”, bot sử dụng self-ping định kỳ nhằm đảm bảo dịch vụ luôn sẵn sàng, đặc biệt khi triển khai trên Render.com.

## Triển khai

### Chuẩn bị môi trường

1. **Lấy Token của Bot Telegram:**
   - Tìm [BotFather](https://core.telegram.org/bots#6-botfather) trên Telegram, tạo bot mới và nhận token.
   - Lưu lại token này cho biến môi trường `TELEGRAM_BOT_TOKEN`.

2. **Lấy API Key của OpenAI:**
   - Truy cập [OpenAI Platform](https://platform.openai.com/account/api-keys), đăng nhập và tạo API key.
   - Lưu lại key cho biến môi trường `OPENAI_API_KEY`.

3. **Cấu hình cơ sở dữ liệu:**  
   Nếu sử dụng PostgreSQL hoặc một hệ quản trị cơ sở dữ liệu khác, hãy tạo database và lấy URL kết nối cho biến `DATABASE_URL`.

4. **Cấu hình URL cho Webhook & Render:**  
   - `WEBHOOK_URL`: URL công khai của endpoint webhook (ví dụ: `https://your-app.onrender.com/webhook`).
   - `RENDER_URL`: URL của ứng dụng trên Render.com (ví dụ: `https://your-app.onrender.com/`).

### Triển khai trên Render.com

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

3. **Thiết lập biến môi trường trên Render Dashboard:**  
   Cấu hình các biến: `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `DATABASE_URL`, `WEBHOOK_URL` và `RENDER_URL`.

---

Với các hướng dẫn trên, bạn đã có thể triển khai một Telegram chat bot tích hợp ChatGPT, đảm bảo duy trì ngữ cảnh trò chuyện thông qua lưu trữ và tóm tắt tin nhắn, đồng thời giữ cho server luôn hoạt động nhờ cơ chế self-ping.
