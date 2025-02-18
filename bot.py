import logging
import asyncio
import os
import time  # Thiếu import cho health_check
import uvicorn  # Thiếu import cho running server
from typing import List, Dict
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, MessageHandler, filters, CallbackContext
from openai import AsyncOpenAI
from pymongo import MongoClient

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cấu hình chat modes: có thể bổ sung thêm các chế độ khác nếu cần
config = {
    "chat_modes": {
         "default": {"parse_mode": "html"},
         "alternative": {"parse_mode": "markdown"}
    },
    "enable_message_streaming": False  # Điều chỉnh theo nhu cầu
}

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

async def get_chat_response(chat_id: int, user_message: str, message_object=None, parse_mode=ParseMode.HTML):
    try:
        recent_messages = list(messages_collection.find(
            {'chat_id': chat_id}
        ).sort('timestamp', -1).limit(MAX_RECENT_MESSAGES))

        messages = [{"role": m['role'], "content": m['content']}
                    for m in recent_messages][::-1]
        messages.append({"role": "user", "content": user_message})

        if len(messages) > MAX_RECENT_MESSAGES:
            summary = await get_chat_summary(messages[:-MAX_RECENT_MESSAGES])
        else:
            summary = ""

        stream = await client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=[{"role": "system", "content": f"Current conversation summary: {summary}"}] + messages,
            stream=True
        )
        
        async def try_edit_message(text: str, current_parse_mode):
            try:
                await message_object.edit_text(text, parse_mode=current_parse_mode)
                return True
            except Exception as e:
                logger.warning(f"Failed to edit message with {current_parse_mode}: {e}")
                return False

        full_response = ""
        buffer = ""
        last_update = ""

        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                buffer += content
                full_response += content

                if len(buffer) >= 50 or any(punct in buffer for punct in ['.', '!', '?', '\n']):
                    if message_object and full_response.strip() and full_response != last_update:
                        # Try HTML first
                        success = await try_edit_message(full_response, ParseMode.HTML)
                        
                        # If HTML fails, try Markdown
                        if not success:
                            success = await try_edit_message(full_response, ParseMode.MARKDOWN_V2)
                            
                        # If both fail, use plain text
                        if not success:
                            try:
                                await message_object.edit_text(full_response, parse_mode=None)
                            except Exception as plain_error:
                                if "Message is not modified" not in str(plain_error):
                                    logger.error(f"Failed to send even plain text: {plain_error}")
                        
                        last_update = full_response
                        buffer = ""
                        await asyncio.sleep(0.01)

        # Final update with the same fallback mechanism
        if message_object and full_response.strip() and full_response != last_update:
            success = await try_edit_message(full_response, ParseMode.HTML)
            if not success:
                success = await try_edit_message(full_response, ParseMode.MARKDOWN_V2)
                if not success:
                    try:
                        await message_object.edit_text(full_response, parse_mode=None)
                    except Exception as final_plain_error:
                        if "Message is not modified" not in str(final_plain_error):
                            logger.error(f"Final update failed with plain text: {final_plain_error}")

        return full_response

    except Exception as e:
        logger.error(f"Error in get_chat_response: {e}")
        return "I'm sorry, there was an error processing your request."

async def handle_message(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text
    if not text:
        return

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        # Try sending initial message with HTML
        try:
            message = await context.bot.send_message(
                chat_id=chat_id,
                text="Đang suy nghĩ...",
                parse_mode=ParseMode.HTML
            )
        except Exception as html_error:
            logger.warning(f"HTML formatting failed: {html_error}")
            try:
                # Try Markdown if HTML fails
                message = await context.bot.send_message(
                    chat_id=chat_id,
                    text="Đang suy nghĩ...",
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            except Exception as md_error:
                logger.warning(f"Markdown formatting failed: {md_error}")
                # Fall back to plain text
                message = await context.bot.send_message(
                    chat_id=chat_id,
                    text="Đang suy nghĩ...",
                    parse_mode=None
                )

        response = await get_chat_response(chat_id, text, message)

        if response and response.strip():
            # The formatting fallback is handled inside get_chat_response
            pass
        else:
            # Try sending error message with fallback formatting
            try:
                await message.edit_text("Xin lỗi, tôi không thể tạo câu trả lời.", parse_mode=ParseMode.HTML)
            except Exception:
                try:
                    await message.edit_text("Xin lỗi, tôi không thể tạo câu trả lời.", parse_mode=ParseMode.MARKDOWN_V2)
                except Exception:
                    await message.edit_text("Xin lỗi, tôi không thể tạo câu trả lời.", parse_mode=None)

    except Exception as e:
        logger.error(f"Error handling message: {e}")
        # Final fallback for error message
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text="Đã xảy ra lỗi, vui lòng thử lại.",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="Đã xảy ra lỗi, vui lòng thử lại.",
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            except Exception:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="Đã xảy ra lỗi, vui lòng thử lại.",
                    parse_mode=None
                )
    #     async for chunk in stream:
    #         if chunk.choices[0].delta.content is not None:
    #             content = chunk.choices[0].delta.content
    #             buffer += content
    #             full_response += content

    #             # Cập nhật khi có sự thay đổi đáng kể
    #             if len(buffer) >= 50 or any(punct in buffer for punct in ['.', '!', '?', '\n']):
    #                 if message_object and full_response.strip() and full_response != last_update:
    #                     try:
    #                         await message_object.edit_text(full_response, parse_mode=parse_mode)
    #                         last_update = full_response  # Cập nhật nội dung cuối
    #                         buffer = ""
    #                         await asyncio.sleep(0.01)
    #                     except Exception as edit_error:
    #                         if "Message is not modified" not in str(edit_error):
    #                             logger.error(f"Error editing message: {edit_error}")

    #     # Cập nhật lần cuối nếu có thay đổi
    #     if message_object and full_response.strip() and full_response != last_update:
    #         try:
    #             await message_object.edit_text(full_response, parse_mode=parse_mode)
    #         except Exception as final_edit_error:
    #             if "Message is not modified" not in str(final_edit_error):
    #                 logger.error(f"Error in final message edit: {final_edit_error}")

    #     # Lưu vào MongoDB
    #     if full_response.strip():
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
    #                 'content': full_response,
    #                 'timestamp': datetime.now()
    #             }
    #         ])

    #     return full_response

    # except Exception as e:
    #     logger.error(f"Error in get_chat_response: {e}")
    #     return "I'm sorry, there was an error processing your request."

# async def handle_message(update: Update, context: CallbackContext):
#     chat_id = update.effective_chat.id
#     text = update.message.text
#     if not text:
#         return

#     # Lấy chat_mode từ cấu hình; ví dụ sử dụng chế độ mặc định "default"
#     chat_mode = "default"
#     # Chọn parse_mode động theo cấu hình
#     parse_mode = {"html": ParseMode.HTML, "markdown": ParseMode.MARKDOWN}[config["chat_modes"][chat_mode]["parse_mode"]]

#     try:
#         await context.bot.send_chat_action(chat_id=chat_id, action="typing")

#         # Gửi tin nhắn placeholder với định dạng dựa theo parse_mode đã chọn
#         message = await context.bot.send_message(
#             chat_id=chat_id,
#             text="Đang suy nghĩ...",
#             parse_mode=parse_mode
#         )

#         response = await get_chat_response(chat_id, text, message, parse_mode=parse_mode)

#         if response and response.strip():
#             try:
#                 # Chỉ cập nhật nếu nội dung khác với placeholder ban đầu
#                 if message.text != response:
#                     await message.edit_text(response, parse_mode=parse_mode)
#             except Exception as e:
#                 if "Message is not modified" not in str(e):
#                     logger.error(f"Error in final update: {e}")
#                     # Nếu không thể edit tin nhắn, gửi tin nhắn mới
#                     await context.bot.send_message(
#                         chat_id=chat_id,
#                         text=response,
#                         parse_mode=parse_mode
#                     )
#         else:
#             await message.edit_text("Xin lỗi, tôi không thể tạo câu trả lời.", parse_mode=parse_mode)

#     except Exception as e:
#         logger.error(f"Error handling message: {e}")
#         await context.bot.send_message(
#             chat_id=chat_id,
#             text="Đã xảy ra lỗi, vui lòng thử lại.",
#             parse_mode=parse_mode
#         )

# Tạo FastAPI app
web_app = FastAPI()

# Khởi tạo Telegram bot Application
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Thêm handler cho tin nhắn văn bản
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Biến lưu trạng thái khởi tạo của ứng dụng
is_initialized = False

@web_app.on_event("startup")
async def on_startup():
    global is_initialized
    if not is_initialized:
        # Tạo index cho MongoDB
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

# Exception handler toàn cục
@web_app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}")
    return JSONResponse(
        status_code=200,  # Trả về 200 thay vì 500
        content={"status": "ok"}
    )

# Middleware xử lý request HEAD
@web_app.middleware("http")
async def handle_head_requests(request: Request, call_next):
    if request.method == "HEAD":
        return JSONResponse(
            status_code=200,
            content={"status": "ok"}
        )
    response = await call_next(request)
    return response

# Route "/" xử lý cả GET và HEAD
@web_app.get("/")
@web_app.head("/")
async def home():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("bot:web_app", host="0.0.0.0", port=port)
