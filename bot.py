import os
import asyncio
import logging
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F, html
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, CommandObject
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

# --- CONFIGURATION (FILL AS NEEDED) ---
TOKEN = "8469807556:AAGjQKCn6FVPGJH5e6U5k5hGEXlEh0c2pZQ"
OWNER_USERNAME = "@DAS_LOVER"  # Admin Username
OWNER_ID = None                # Integer ID (Optional, better for reliable DMs)
CHANNEL_USERNAME = "@doraemonandshinchanmoviess"
NETFLIX_LOGO = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Netflix_2015_logo.svg/2560px-Netflix_2015_logo.svg.png"

# --- DB (Memory Persistence) ---
MEMORY_DB = {"users": {}}

# --- BOT LOGIC ---
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
    user = message.from_user
    args = command.args
    referrer_id = int(args) if args and args.isdigit() and int(args) != user.id else None
    
    # 1. Register User
    is_new = await create_user(user.id, user.username, user.full_name, referrer_id)
    
    # 2. Add Points to Referrer
    if is_new and referrer_id and referrer_id in MEMORY_DB["users"]:
         MEMORY_DB["users"][referrer_id]["referrals"] += 1
         # Notify Referrer
         try:
             curr = MEMORY_DB["users"][referrer_id]["referrals"]
             await bot.send_message(referrer_id, f"🎉 <b>New Referral!</b>\n{user.full_name} joined.\nPoints: {curr}/5")
         except: pass

    await show_dashboard(message, user)

async def show_dashboard(message: Message, user):
    user_data = await get_user(user.id)
    points = user_data['referrals'] if user_data else 0
    username = (await message.bot.get_me()).username
    invite_link = f"https://t.me/{username}?start={user.id}"
    
    welcome_text = (
        f"Namaste {html.bold(user.full_name)}! 👋\n\n"
        f"🎉 <b>Share & Win Rewards Bot</b>\n"
        f"Free Premium Rewards jeetne ke liye step complete karein.\n\n"
        f"👇 <b>TASK: Invite 5 Friends</b>\n"
        f"Link share karein aur points jeetein.\n\n"
        f"🔗 <b>Your Link:</b>\n<code>{invite_link}</code>\n\n"
        f"🏆 <b>Your Points:</b> {points}/5\n\n"
        f"(Jaise hi 5 points honge, 'Redeem' button kaam karega!)"
    )
    
    btn_text = "🔒 Redeem (Need 5 Points)" if points < 5 else "🎁 REDEEM REWARD NOW"
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
    try: await callback.message.delete()
    except: pass
    await show_dashboard(callback.message, callback.from_user)

@router.callback_query(F.data == "redeem_locked")
async def redeem_locked(callback: CallbackQuery):
    user_data = await get_user(callback.from_user.id)
    points = user_data['referrals'] if user_data else 0
    rem = 5 - points
    await callback.answer(f"❌ {points}/5 Points.\n{rem} aur chahiye!", show_alert=True)

@router.callback_query(F.data == "redeem_now")
async def redeem_now(callback: CallbackQuery, bot: Bot):
    user = callback.from_user
    # Security Check
    user_data = await get_user(user.id)
    if not user_data or user_data['referrals'] < 5:
         return await redeem_locked(callback)

    # Note: Channel check is skipped to avoid crashing if bot isn't admin
    # Notify Owner
    recipient = OWNER_ID if OWNER_ID else OWNER_USERNAME
    msg = f"✅ <b>REDEEM REQUEST!</b>\nUser: {user.full_name} (@{user.username})\nID: <code>{user.id}</code>\n<b>Status:</b> Completed 5 Referrals."
    
    try: await bot.send_message(recipient, msg)
    except: pass
    
    await callback.message.edit_caption(caption="✅ <b>Request Sent!</b>\n\nAdmin will contact you soon.", reply_markup=None)

# --- RENDER WEB SERVER (DUMMY) ---
async def health(request):
    return web.Response(text="Bot Alive")

async def main():
    # 1. Setup Bot
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    # 2. Start Web Server (For Render Port Binding)
    app = web.Application()
    app.add_routes([web.get('/', health)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080)) # Render passes PORT automatically
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server started on port {port}")

    # 3. Clean Webhook & Start Polling
    print("Deleting old webhook...")
    await bot.delete_webhook(drop_pending_updates=True)
    print("Starting Polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
