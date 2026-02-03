from http.server import BaseHTTPRequestHandler
import json
import asyncio
import os
import sys

# Add root directory to sys.path so we can import bot.py
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
import bot as bot_module 

TOKEN = "8207872443:AAHxbq29c3zt58N5Rqu_9KgHQyrEyV1l-3o"

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
            
            async def process_update():
                bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
                dp = Dispatcher(storage=MemoryStorage())
                # Include Router
                dp.include_router(bot_module.router)

                update = Update.model_validate(data, context={"bot": bot})
                await dp.feed_update(bot, update)
                await bot.session.close()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_update())
            loop.close()

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
            
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode())

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running! (Standard Vercel Structure)")
