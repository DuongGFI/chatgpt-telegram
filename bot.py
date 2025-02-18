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

# async def get_chat_response(chat_id: int, user_message: str) -> str:
#     try:
#         # Lấy tin nhắn gần đây từ MongoDB
#         recent_messages = list(messages_collection.find(
#             {'chat_id': chat_id}
#         ).sort('timestamp', -1).limit(MAX_RECENT_MESSAGES))

#         messages = [{"role": m['role'], "content": m['content']}
#                    for m in recent_messages][::-1]  # Đảo ngược để có thứ tự đúng

#         messages.append({"role": "user", "content": user_message})

#         if len(messages) > MAX_RECENT_MESSAGES:
#             summary = await get_chat_summary(messages[:-MAX_RECENT_MESSAGES])
#         else:
#             summary = ""

#         response = await client.chat.completions.create(
#             model="gpt-3.5-turbo-16k",
#             messages=[{"role": "system", "content": f"Current conversation summary: {summary}"}]
#                     + messages,
#         )

#         assistant_message = response.choices[0].message.content or "I'm sorry, I couldn't generate a response."

#         # Lưu tin nhắn vào MongoDB
#         messages_collection.insert_many([
#             {
#                 'chat_id': chat_id,
#                 'role': "user",
#                 'content': user_message,
#                 'timestamp': datetime.now()
#             },
#             {
#                 'chat_id': chat_id,
#                 'role': "assistant",
#                 'content': assistant_message,
#                 'timestamp': datetime.now()
#             }
#         ])

#         return assistant_message
#     except Exception as e:
#         logger.error(f"Error in get_chat_response: {e}")
#         return "I'm sorry, there was an error processing your request."

# async def handle_message(update: Update, context: CallbackContext):
#     chat_id = update.effective_chat.id
#     text = update.message.text
#     if not text:
#         return
#     try:
#         response = await get_chat_response(chat_id, text)
#         await context.bot.send_message(chat_id=chat_id, text=response)
#     except Exception as e:
#         logger.error(f"Error handling message: {e}")
#         await context.bot.send_message(
#             chat_id=chat_id,
#             text="I'm sorry, an error occurred."
#         )

async def send_message(self, chat_id: int, text: str) -> None:
    """
    Send message to telegram chat with typing action and streaming
    """
    try:
        # Show typing action
        await self.bot.send_chat_action(chat_id=chat_id, action="typing")

        # Split message into chunks if too long
        if len(text) > 4096:
            chunks = [text[i:i+4096] for i in range(0, len(text), 4096)]

            # Send first chunk as initial message
            message = await self.bot.send_message(
                chat_id=chat_id,
                text=chunks[0][:20] + "..." # Initial preview
            )

            # Stream remaining chunks
            current_text = chunks[0]
            for chunk in chunks:
                current_text += chunk
                await asyncio.sleep(0.01) # Small delay between updates
                try:
                    await message.edit_text(current_text)
                except Exception as e:
                    logger.error(f"Failed to edit message: {e}")
                    continue

        else:
            # For shorter messages, show typing then send full message
            message = await self.bot.send_message(
                chat_id=chat_id,
                text="..." # Initial placeholder
            )

            # Stream the message character by character
            current_text = ""
            for char in text:
                current_text += char
                if len(current_text) % 5 == 0: # Update every 5 chars
                    try:
                        await message.edit_text(current_text)
                        await asyncio.sleep(0.01)
                    except Exception as e:
                        logger.error(f"Failed to edit message: {e}")
                        continue

            # Ensure final message is complete
            try:
                await message.edit_text(text)
            except Exception as e:
                logger.error(f"Failed to edit final message: {e}")

    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        # Fallback to simple message if streaming fails
        await self.bot.send_message(chat_id=chat_id, text=text)

# Sửa hàm handle_message để sử dụng send_message mới
async def handle_message(self, update: Update, context: CallbackContext) -> None:
    """
    Handle incoming messages
    """
    if update.edited_message is not None:
        return

    chat_id = update.effective_chat.id
    # user_id = update.effective_user.id

    if update.message.text is None:
        return

    async with self.semaphore:
        try:
            # Show typing indicator
            await self.bot.send_chat_action(chat_id=chat_id, action="typing")

            # Get response from ChatGPT
            response = await self.chatgpt.send_message(
                update.message.text,
                chat_id=chat_id,
                user_id=user_id
            )

            # Send response with streaming
            await self.send_message(chat_id, response)

        except Exception as e:
            error_text = f"Error: {str(e)}"
            logger.error(error_text)
            await self.bot.send_message(
                chat_id=chat_id,
                text=error_text
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

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("bot:web_app", host="0.0.0.0", port=port)
