from http.server import BaseHTTPRequestHandler
import json
import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Update
from aiogram.fsm.storage.memory import MemoryStorage

# --- CONFIGURATION (ALL IN ONE) ---
TOKEN = "8207872443:AAHxbq29c3zt58N5Rqu_9KgHQyrEyV1l-3o"
OWNER_USERNAME = "@DAS_LOVER" 
OWNER_ID = None 
CHANNEL_USERNAME = "@doraemonandshinchanmoviess"
NETFLIX_LOGO = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Netflix_2015_logo.svg/2560px-Netflix_2015_logo.svg.png"

# --- MEMORY DB ---
MEMORY_DB = {"users": {}}

# --- LOGIC ---
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

async def increment_display_referral(user_id):
    if user_id in MEMORY_DB["users"]:
        MEMORY_DB["users"][user_id]["referrals"] += 1

@router.message(CommandStart())
async def command_start_handler(message: Message, command: CommandObject, bot: Bot):
    user = message.from_user
    args = command.args
    referrer_id = int(args) if args and args.isdigit() and int(args) != user.id else None
    
    is_new = await create_user(user.id, user.username, user.full_name, referrer_id)
    
    if is_new and referrer_id:
        await increment_display_referral(referrer_id)
        try:
            referrer_mb = await get_user(referrer_id)
            if referrer_mb:
                curr_points = referrer_mb['referrals']
                await bot.send_message(
                    chat_id=referrer_id, 
                    text=f"🥳 <b>New Referral!</b>\n\n{user.full_name} ne aapke link se join kiya.\nTotal Points: {curr_points}/5"
                )
        except: pass
            
    await show_dashboard(message, user)

async def show_dashboard(message: Message, user):
    user_data = await get_user(user.id)
    points = user_data['referrals'] if user_data else 0
    invite_link = f"https://t.me/{(await message.bot.get_me()).username}?start={user.id}"
    
    welcome_text = (
        f"Namaste {html.bold(user.full_name)}! 👋\n\n"
        f"🎉 <b>Netflix Giveaway Bot</b>\n"
        f"Free Netflix account jeetne ke liye step complete karein.\n\n"
        f"👇 <b>TASK: Invite 5 Friends</b>\n"
        f"Apne doston ko niche diye gaye link se invite karein.\n\n"
        f"🔗 <b>Your Link:</b>\n<code>{invite_link}</code>\n\n"
        f"🏆 <b>Your Points:</b> {points}/5\n\n"
        f"(Jaise hi 5 points honge, 'Redeem' button kaam karega!)"
    )
    
    btn_text = "🔒 Redeem (Need 5 Points)" if points < 5 else "🎁 REDEEM NETFLIX NOW"
    cbd = "redeem_locked" if points < 5 else "redeem_now"
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Join Channel First", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton(text="🔄 Check Points", callback_data="check_points")],
        [InlineKeyboardButton(text=btn_text, callback_data=cbd)]
    ])
    
    try: await message.answer_photo(photo=NETFLIX_LOGO, caption=welcome_text, reply_markup=keyboard)
    except: await message.answer(text=welcome_text, reply_markup=keyboard)

@router.callback_query(F.data == "check_points")
async def check_stats(callback: CallbackQuery):
    await callback.answer("Refreshing...")
    await callback.message.delete()
    await show_dashboard(callback.message, callback.from_user)

@router.callback_query(F.data == "redeem_locked")
async def redeem_locked(callback: CallbackQuery):
    user_data = await get_user(callback.from_user.id)
    points = user_data['referrals'] if user_data else 0
    remaining = 5 - points
    await callback.answer(f"❌ Abhi {points}/5 points hain.\n{remaining} aur invite chahiye!", show_alert=True)

@router.callback_query(F.data == "redeem_now")
async def redeem_now(callback: CallbackQuery, bot: Bot):
    user = callback.from_user
    user_data = await get_user(user.id)
    if not user_data or user_data['referrals'] < 5:
        return await redeem_locked(callback)
    
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user.id)
        if member.status in ["left", "kicked"]:
            await callback.answer("⚠️ Pehle Channel Join Karein!", show_alert=True)
            return
    except: pass
        
    recipient = OWNER_ID if OWNER_ID else OWNER_USERNAME
    msg = f"✅ <b>REDEEM REQUEST!</b>\nUser: {user.full_name} (@{user.username})\nID: <code>{user.id}</code>\nStatus: Completed 5 Referrals."
    
    try: await bot.send_message(recipient, msg)
    except: pass
    
    await callback.message.edit_caption(caption="✅ <b>Request Sent!</b>\n\nAdmin ko request bhej di gayi hai.", reply_markup=None)

# --- WEBHOOK HANDLER ---
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data)
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
            self.send_response(500); self.end_headers(); self.wfile.write(f"Error: {e}".encode())

    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"Bot is Running! (Standalone Mode)")
