import logging
import asyncio
import os
import time  # Thiếu import cho health_check
import uvicorn  # Thiếu import cho running server
from typing import List, Dict
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext
from openai import AsyncOpenAI
from pymongo import MongoClient
from keep_alive import keep_alive, start_ping


# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lấy thông tin từ biến môi trường
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")  # MongoDB Atlas connection string
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Khởi tạo OpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Kết nối MongoDB
try:
    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client['telegram_bot']
    messages_collection = db['chat_history']
    # Test connection
    mongo_client.server_info()
except Exception as e:
    logger.error(f"MongoDB connection failed: {e}")
    raise
    
MAX_RECENT_MESSAGES = 10
CONTEXT_UPDATE_INTERVAL = 5 * 60
SUMMARY_PROMPT = (
    "You are a helpful assistant. Summarize the following conversation, "
    "focusing on key details, user preferences, and important information "
    "to maintain consistent context:"
)

async def get_chat_summary(messages: List[Dict[str, str]]) -> str:
    prompt = f"{SUMMARY_PROMPT}\n\n" + "\n".join(
        f"{m['role']}: {m['content']}" for m in messages
    )
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=200,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"Error in get_chat_summary: {e}")
        return "Error generating summary."

async def get_chat_response(chat_id: int, user_message: str) -> str:
    try:
        # Lấy tin nhắn gần đây từ MongoDB
        recent_messages = list(messages_collection.find(
            {'chat_id': chat_id}
        ).sort('timestamp', -1).limit(MAX_RECENT_MESSAGES))

        messages = [{"role": m['role'], "content": m['content']}
                   for m in recent_messages][::-1]  # Đảo ngược để có thứ tự đúng

        messages.append({"role": "user", "content": user_message})

        if len(messages) > MAX_RECENT_MESSAGES:
            summary = await get_chat_summary(messages[:-MAX_RECENT_MESSAGES])
        else:
            summary = ""

        response = await client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=[{"role": "system", "content": f"Current conversation summary: {summary}"}]
                    + messages,
        )

        assistant_message = response.choices[0].message.content or "I'm sorry, I couldn't generate a response."

        # Lưu tin nhắn vào MongoDB
        messages_collection.insert_many([
            {
                'chat_id': chat_id,
                'role': "user",
                'content': user_message,
                'timestamp': datetime.now()
            },
            {
                'chat_id': chat_id,
                'role': "assistant",
                'content': assistant_message,
                'timestamp': datetime.now()
            }
        ])

        return assistant_message
    except Exception as e:
        logger.error(f"Error in get_chat_response: {e}")
        return "I'm sorry, there was an error processing your request."

async def handle_message(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text
    if not text:
        return
    try:
        response = await get_chat_response(chat_id, text)
        await context.bot.send_message(chat_id=chat_id, text=response)
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="I'm sorry, an error occurred."
        )

# Tạo FastAPI app
web_app = FastAPI()

# Khởi tạo Telegram bot Application
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Thêm handlers
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Biến để lưu trữ trạng thái khởi tạo
is_initialized = False

@web_app.on_event("startup")
async def on_startup():
    global is_initialized
    if not is_initialized:
        # Create indexes
        messages_collection.create_index([("chat_id", 1)])
        messages_collection.create_index([("timestamp", -1)])
        await telegram_app.initialize()
        if WEBHOOK_URL:
            await telegram_app.bot.set_webhook(WEBHOOK_URL)
            logger.info(f"Webhook set to {WEBHOOK_URL}")
        is_initialized = True
    else:
        logger.info("Application already initialized")

@web_app.on_event("shutdown")
async def on_shutdown():
    global is_initialized
    try:
        if is_initialized:
            await telegram_app.shutdown()
            await telegram_app.bot.delete_webhook()
            mongo_client.close()
            logger.info("Webhook deleted and application shut down")
            is_initialized = False
    except Exception as e:
        logger.error(f"Failed to shut down properly: {e}")

@web_app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        update_data = await request.json()
        update = Update.de_json(update_data, telegram_app.bot)
        await telegram_app.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@web_app.get("/")
async def home():
    return "Bot is alive!"

@web_app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "uptime": "active"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    keep_alive()
    start_ping()
    uvicorn.run("bot:web_app", host="0.0.0.0", port=port)
