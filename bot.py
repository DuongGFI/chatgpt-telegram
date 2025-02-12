import logging
import asyncio
import time
import os
from typing import List, Dict
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext
import openai
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from keep_alive import start_keep_alive

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lấy thông tin từ biến môi trường
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
openai.api_key = OPENAI_API_KEY

# Cấu hình database
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, index=True)
    role = Column(String, index=True)
    content = Column(Text)

Base.metadata.create_all(engine)

MAX_RECENT_MESSAGES = 10  # Lưu nhiều tin nhắn hơn để cải thiện ngữ cảnh
CONTEXT_UPDATE_INTERVAL = 5 * 60  # 5 phút

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
        response = await asyncio.to_thread(
            openai.ChatCompletion.create,
            model="gpt-3.5-turbo-16k",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=200,
        )
        return response["choices"][0]["message"]["content"] or ""
    except Exception as e:
        logger.error(f"Error in get_chat_summary: {e}")
        return "Error generating summary."

async def get_chat_response(chat_id: int, user_message: str) -> str:
    session = SessionLocal()
    messages = session.query(ChatHistory).filter(ChatHistory.chat_id == chat_id).all()
    messages = [{"role": m.role, "content": m.content} for m in messages]
    
    if "search:" in user_message.lower():
        search_query = user_message.split("search:", 1)[1].strip()
        return google_search(search_query)
    
    messages.append({"role": "user", "content": user_message})
    if len(messages) > MAX_RECENT_MESSAGES:
        messages.pop(0)
    
    summary = await get_chat_summary(messages)
    
    try:
        response = await asyncio.to_thread(
            openai.ChatCompletion.create,
            model="gpt-3.5-turbo-16k",
            messages=[{"role": "system", "content": f"Current conversation summary: {summary}"}] + messages,
        )
        assistant_message = response["choices"][0]["message"]["content"] or "I'm sorry, I couldn't generate a response."
        
        session.add(ChatHistory(chat_id=chat_id, role="user", content=user_message))
        session.add(ChatHistory(chat_id=chat_id, role="assistant", content=assistant_message))
        session.commit()
        session.close()
        
        return assistant_message
    except Exception as e:
        logger.error(f"Error in get_chat_response: {e}")
        return "I'm sorry, there was an error processing your request."

async def handle_message(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    text = update.message.text
    
    if not text:
        return
    
    try:
        response = await get_chat_response(chat_id, text)
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("I'm sorry, an error occurred.")

def main():
    start_keep_alive()  # Giữ bot luôn online
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Telegram bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
