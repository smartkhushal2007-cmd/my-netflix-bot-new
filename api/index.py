from http.server import BaseHTTPRequestHandler
import json
import asyncio
import sys
import traceback

# Print to stdout for Vercel Logs
def log(msg):
    print(msg, file=sys.stdout)

try:
    from aiogram import Bot, Dispatcher, Router, F, html
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    from aiogram.filters import CommandStart, CommandObject
    from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Update
    from aiogram.fsm.storage.memory import MemoryStorage
except ImportError as e:
    log(f"CRITICAL IMPORT ERROR: {e}")
    raise e

# --- CONFIGURATION ---
TOKEN = "8207872443:AAHxbq29c3zt58N5Rqu_9KgHQyrEyV1l-3o"
OWNER_USERNAME = "@DAS_LOVER" 
OWNER_ID = None 
CHANNEL_USERNAME = "@doraemonandshinchanmoviess"
NETFLIX_LOGO = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Netflix_2015_logo.svg/2560px-Netflix_2015_logo.svg.png"

# --- MEMORY DB ---
MEMORY_DB = {"users": {}}
router = Router()

async def get_user(user_id):
    return MEMORY_DB["users"].get(user_id)

async def create_user(user_id, username, full_name, referrer_id=None):
    if user_id not in MEMORY_DB["users"]:
        MEMORY_DB["users"][user_id] = {
            "user_id": user_id, "username": username, "full_name": full_name, 
            "referrals": 0, "referrer_id": referrer_id
        }
        return True
    return False

@router.message(CommandStart())
async def command_start_handler(message: Message, command: CommandObject, bot: Bot):
    log(f"Handling /start for {message.from_user.id}")
    user = message.from_user
    args = command.args
    referrer_id = int(args) if args and args.isdigit() and int(args) != user.id else None
    
    await create_user(user.id, user.username, user.full_name, referrer_id)
    await show_dashboard(message, user)

async def show_dashboard(message: Message, user):
    user_data = await get_user(user.id)
    points = user_data['referrals'] if user_data else 0
    invite_link = f"https://t.me/{(await message.bot.get_me()).username}?start={user.id}"
    
    welcome_text = (
        f"Namaste {html.bold(user.full_name)}! 👋\n\n"
        f"🎉 <b>Netflix Giveaway Bot</b>\n\n"
        f"👇 <b>TASK: Invite 5 Friends</b>\n"
        f"🔗 <b>Link:</b> <code>{invite_link}</code>\n"
        f"🏆 <b>Points:</b> {points}/5"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Check Points", callback_data="check_points")]
    ])
    try: await message.answer_photo(photo=NETFLIX_LOGO, caption=welcome_text, reply_markup=keyboard)
    except: await message.answer(text=welcome_text, reply_markup=keyboard)

@router.callback_query(F.data == "check_points")
async def check_stats(callback: CallbackQuery):
    await callback.answer("Refreshing...")
    await show_dashboard(callback.message, callback.from_user)

# --- WEBHOOK HANDLER ---
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
            log(f"Received Update: {data.get('update_id')}")
            
            async def process_update():
                bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
                dp = Dispatcher(storage=MemoryStorage())
                dp.include_router(router)
                
                update = Update.model_validate(data, context={"bot": bot})
                await dp.feed_update(bot, update)
                await bot.session.close()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_update())
            loop.close()
            
            self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
        except Exception as e:
            log(f"ERROR: {e}\n{traceback.format_exc()}")
            self.send_response(500); self.end_headers(); self.wfile.write(f"Error: {e}".encode())

    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"Bot is Running! (Logged Mode)")
