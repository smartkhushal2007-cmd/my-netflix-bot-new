from http.server import BaseHTTPRequestHandler
import json
import asyncio
import sys
import traceback

# --- CONFIGURATION ---
TOKEN = "8207872443:AAHxbq29c3zt58N5Rqu_9KgHQyrEyV1l-3o"
CHANNEL_USERNAME = "@doraemonandshinchanmoviess"
OWNER_ID = 5110196726 # Hardcoded Owner ID (Anmol) to work without DB
NETFLIX_LOGO = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Netflix_2015_logo.svg/2560px-Netflix_2015_logo.svg.png"

# --- IMPORTS ---
try:
    from aiogram import Bot, Dispatcher, Router, F, html
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    from aiogram.filters import CommandStart, CommandObject
    from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Update
    from aiogram.fsm.storage.memory import MemoryStorage
except ImportError as e:
    print(f"IMPORT ERROR: {e}")

# --- LOGIC ---
router = Router()

@router.message(CommandStart())
async def start_handler(message: Message, command: CommandObject):
    user = message.from_user
    args = command.args
    invite_link = f"https://t.me/{(await message.bot.get_me()).username}?start={user.id}"
    
    # Simple Logic: Just show the interface. 
    # Validating referrals on Vercel Memory is flaky, so we simplify for stability first.
    
    welcome_text = (
        f"Namaste {html.bold(user.full_name)}! 👋\n\n"
        f"🎉 <b>Netflix Giveaway Bot</b>\n\n"
        f"👇 <b>TASK: Invite 5 Friends</b>\n"
        f"🔗 <b>Link:</b> <code>{invite_link}</code>\n"
        f"🏆 <b>Points:</b> 0/5 (Demo Mode on Serverless)"
    )
    
    btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Check Points", callback_data="check")]])
    try: await message.answer_photo(photo=NETFLIX_LOGO, caption=welcome_text, reply_markup=btn)
    except: await message.answer(text=welcome_text, reply_markup=btn)

@router.callback_query(F.data == "check")
async def check_btn(callback: CallbackQuery):
    await callback.answer("Serverless Mode: Points reset on reload.", show_alert=True)

# --- EXECUTION ---
async def main_async(data):
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    try:
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot, update)
    finally:
        await bot.session.close()

# --- HANDLER ---
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
            # Create a new event loop for this request
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(main_async(data))
            loop.close()
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        except Exception as e:
            print(f"CRASH: {e}")
            traceback.print_exc()
            self.send_response(200) # Send 200 even on error to stop Telegram from retrying
            self.end_headers()
            self.wfile.write(b"Error")

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Deepseek Bot Running!")
