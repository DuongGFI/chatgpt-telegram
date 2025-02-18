# ChatGPT Telegram Bot với MongoDB Atlas

Bot Telegram tích hợp ChatGPT với khả năng lưu trữ và quản lý ngữ cảnh trò chuyện thông minh. Sử dụng MongoDB Atlas để lưu trữ tin nhắn và tự động tóm tắt các cuộc trò chuyện dài nhằm duy trì ngữ cảnh hiệu quả.

## ✨ Tính Năng Chính

### 1. Quản Lý Ngữ Cảnh Thông Minh
- Lưu trữ 10 tin nhắn gần nhất để duy trì ngữ cảnh trò chuyện ngắn hạn.
- Tự động tóm tắt các tin nhắn cũ khi vượt quá giới hạn.
- Tích hợp ngữ cảnh vào phản hồi nhằm đảm bảo câu trả lời luôn nhất quán.

### 2. Hệ Thống Lưu Trữ MongoDB Atlas
- Lưu trữ tin nhắn với cấu trúc NoSQL linh hoạt.
- Ghi nhận timestamp cho mỗi tin nhắn để quản lý thời gian thực.
- Truy vấn hiệu quả các tin nhắn gần đây.

### 3. Cơ Chế Tóm Tắt Thông Minh
- Sử dụng một prompt tóm tắt đặc biệt (SUMMARY_PROMPT) để hướng dẫn ChatGPT tóm tắt cuộc trò chuyện, tập trung vào các chi tiết quan trọng, sở thích của người dùng và thông tin cần thiết nhằm duy trì ngữ cảnh.

## 🛠 Cài Đặt và Triển Khai

### Yêu Cầu Hệ Thống
- `python-telegram-bot>=20.0`
- `fastapi>=0.68.0`
- `uvicorn>=0.15.0`
- `openai>=1.0.0`
- `pymongo>=4.0.0`
- `python-dotenv>=0.19.0`

### Biến Môi Trường

Tạo file `.env` với nội dung:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
MONGODB_URI=your_mongodb_connection_string
WEBHOOK_URL=your_webhook_url
```

### Triển Khai Local

```bash
# Clone repository
git clone https://github.com/your-username/chatgpt-telegram.git

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy bot
python bot.py
```

### Triển Khai trên Render.com

#### Chuẩn Bị Repository
- Push code lên GitHub và đảm bảo đầy đủ các file cần thiết.

#### Tạo Web Service trên Render
- Đăng nhập vào Render.com.
- Chọn **New + → Web Service** và connect với GitHub repository.

#### Cấu Hình Service
- **Name:** chatgpt-telegram-bot  
- **Environment:** Python 3  
- **Build Command:** `pip install -r requirements.txt`  
- **Start Command:** `python bot.py`

#### Environment Variables
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
MONGODB_URI=your_mongodb_connection_string
WEBHOOK_URL=https://your-app-name.onrender.com/webhook
RENDER_URL=https://your-app-name.onrender.com
```

## 💾 Cấu Trúc Dữ Liệu

**Collection:** `chat_history`

```json
{
    "chat_id": "Integer,      // ID cuộc trò chuyện Telegram",
    "role": "String,          // 'user' hoặc 'assistant'",
    "content": "String,       // Nội dung tin nhắn",
    "timestamp": "DateTime    // Thời gian gửi tin nhắn"
}
```

## 🔍 Monitoring và Troubleshooting

### Health Check Endpoint
- Có một endpoint `/health` kiểm tra trạng thái của hệ thống, trả về thông tin về:
  - **status:** trạng thái tổng thể.
  - **database:** kết nối đến MongoDB.
  - **bot:** trạng thái hoạt động của bot.

### Common Issues

#### Webhook Errors
- Kiểm tra lại `WEBHOOK_URL`.
- Xác minh chứng chỉ SSL.
- Kiểm tra phản hồi từ API Telegram.

#### Database Connection
- Kiểm tra giá trị của `MONGODB_URI`.
- Xem xét cài đặt Network Access.
- Theo dõi trạng thái kết nối.

## 📝 License

Phân phối theo giấy phép MIT. Xem file `LICENSE` để biết thêm chi tiết.

⭐️ From Dương Nguyễn
