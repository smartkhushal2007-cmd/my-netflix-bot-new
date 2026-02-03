import asyncio
import logging
import sys
from os import getenv

import aiosqlite
from aiogram import Bot, Dispatcher, Router, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.fsm.storage.memory import MemoryStorage

# --- CONFIGURATION ---
TOKEN = "8207872443:AAHxbq29c3zt58N5Rqu_9KgHQyrEyV1l-3o"
OWNER_USERNAME = "@DAS_LOVER" 
OWNER_ID = None # Replace with integer ID if known
CHANNEL_USERNAME = "@doraemonandshinchanmoviess"
NETFLIX_LOGO = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Netflix_2015_logo.svg/2560px-Netflix_2015_logo.svg.png"

DB_NAME = "giveaway_bot.db"

# Logging setup
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# --- DATABASE ---
# Vercel Memory Fallback
USE_MEMORY_DB = getenv("VERCEL") is not None
MEMORY_DB = {"users": {}} 

async def init_db():
    if USE_MEMORY_DB: return
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                referrals INTEGER DEFAULT 0,
                referrer_id INTEGER,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def get_user(user_id):
    if USE_MEMORY_DB:
        return MEMORY_DB["users"].get(user_id)
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {"user_id": row[0], "username": row[1], "full_name": row[2], "referrals": row[3], "referrer_id": row[4]}
            return None

async def create_user(user_id, username, full_name, referrer_id=None):
    if USE_MEMORY_DB:
        if user_id not in MEMORY_DB["users"]:
            MEMORY_DB["users"][user_id] = {
                "user_id": user_id, "username": username, "full_name": full_name, 
                "referrals": 0, "referrer_id": referrer_id
            }
            return True # New user created
        return False # User already exists

    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute(
                "INSERT INTO users (user_id, username, full_name, referrals, referrer_id) VALUES (?, ?, ?, 0, ?)",
                (user_id, username, full_name, referrer_id)
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

async def increment_referral(user_id):
    if USE_MEMORY_DB:
        if user_id in MEMORY_DB["users"]:
            MEMORY_DB["users"][user_id]["referrals"] += 1
        return

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id = ?", (user_id,))
        await db.commit()

# --- HANDLERS ---
router = Router()

@router.message(CommandStart())
async def command_start_handler(message: Message, command: CommandObject, bot: Bot):
    user = message.from_user
    args = command.args
    referrer_id = int(args) if args and args.isdigit() and int(args) != user.id else None
    
    is_new = await create_user(user.id, user.username, user.full_name, referrer_id)
    
    if is_new and referrer_id:
        # Notify referrer and add point
        await increment_referral(referrer_id)
        try:
            referrer_mb = await get_user(referrer_id)
            if referrer_mb:
                curr_points = referrer_mb['referrals'] + 1 # +1 because we just added it but db read might be stale or we just want to show current
                await bot.send_message(
                    chat_id=referrer_id, 
                    text=f"🥳 <b>New Referral!</b>\n\n{user.full_name} ne aapke link se join kiya.\nTotal Points: {curr_points}/5"
                )
        except Exception as e:
            pass # Referrer might have blocked bot
            
    # Show Dashboard
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
    
    # Conditional Redeem Button
    btn_text = "🔒 Redeem (Need 5 Points)"
    cbd = "redeem_locked"
    if points >= 5:
        btn_text = "🎁 REDEEM NETFLIX NOW"
        cbd = "redeem_now"
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Join Channel First", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton(text="🔄 Check Points", callback_data="check_points")],
        [InlineKeyboardButton(text=btn_text, callback_data=cbd)]
    ])
    
    # Send as Photo logic
    try:
        await message.answer_photo(photo=NETFLIX_LOGO, caption=welcome_text, reply_markup=keyboard)
    except:
         # Fallback if photo fails or edits
         await message.answer(text=welcome_text, reply_markup=keyboard)

@router.callback_query(F.data == "check_points")
async def check_stats(callback: CallbackQuery):
    await callback.answer("Refreshing...")
    # Delete old message to send fresh with photo or edit caption
    await callback.message.delete()
    await show_dashboard(callback.message, callback.from_user)

@router.callback_query(F.data == "redeem_locked")
async def redeem_locked(callback: CallbackQuery):
    user_data = await get_user(callback.from_user.id)
    points = user_data['referrals']
    remaining = 5 - points
    await callback.answer(f"❌ Abhi {points}/5 points hain.\n{remaining} aur invite chahiye!", show_alert=True)

@router.callback_query(F.data == "redeem_now")
async def redeem_now(callback: CallbackQuery, bot: Bot):
    user = callback.from_user
    
    # Security: Double check points on server side
    user_data = await get_user(user.id)
    if not user_data or user_data['referrals'] < 5:
        return await redeem_locked(callback)
    
    # Verification: Check channel join
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user.id)
        if member.status in ["left", "kicked"]:
            await callback.answer("⚠️ Pehle Channel Join Karein!", show_alert=True)
            return
    except:
        pass # Skip check if bot not admin
        
    # Notify Owner
    recipient = OWNER_ID if OWNER_ID else OWNER_USERNAME
    msg = (
        f"✅ <b>REDEEM REQUEST!</b>\n\n"
        f"User: {user.full_name} (@{user.username})\n"
        f"ID: <code>{user.id}</code>\n"
        f"Status: Completed 5 Referrals.\n\n"
        f"⚠️ <b>Action:</b> Please send Netflix ID/Pass to this user."
    )
    
    try:
        if isinstance(recipient, int):
            await bot.send_message(recipient, msg)
        else:
             await bot.send_message(recipient, msg)
        
        await callback.message.edit_caption(
            caption="✅ <b>Request Sent!</b>\n\nAdmin ko request bhej di gayi hai. Wo aapko jald hi DM karenge.\n\nStay tuned! 🍿",
            reply_markup=None
        )
    except Exception as e:
        logger.error(f"Failed to send to owner: {e}")
        await callback.answer("Error sending request. Try again later.", show_alert=True)


# --- MAIN ---
async def start_polling():
    await init_db()
    
    logger.info("Bot is starting (Polling)...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

# Global instances
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)) # CHANGED TO HTML
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)

if __name__ == "__main__":
    try:
        asyncio.run(start_polling())
    except KeyboardInterrupt:
        logger.info("Bot stopped!")
