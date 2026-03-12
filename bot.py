import os
import asyncio
import logging
import sys
import aiosqlite
from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F, html
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, CommandObject
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

# --- CONFIGURATION ---
TOKEN = "8469807556:AAGjQKCn6FVPGJH5e6U5k5hGEXlEh0c2pZQ"
OWNER_USERNAME = "@DAS_LOVER"
OWNER_ID = None  # Set your Telegram numeric ID here for reliable notifications e.g. 123456789
CHANNEL_USERNAME = "@doraemonandshinchanmoviess"
NETFLIX_LOGO = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Netflix_2015_logo.svg/2560px-Netflix_2015_logo.svg.png"
DB_PATH = "bot_data.db"

router = Router()

# ==================== DATABASE ====================

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                referrals INTEGER DEFAULT 0,
                referrer_id INTEGER,
                redeemed INTEGER DEFAULT 0
            )
        """)
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

async def create_user(user_id, username, full_name, referrer_id=None):
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO users (user_id, username, full_name, referrer_id) VALUES (?, ?, ?, ?)",
                (user_id, username, full_name, referrer_id)
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False  # Already exists

async def increment_referral(referrer_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id = ?", (referrer_id,))
        await db.commit()

async def mark_redeemed(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET redeemed = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

# ==================== HANDLERS ====================

@router.message(CommandStart())
async def command_start_handler(message: Message, command: CommandObject, bot: Bot):
    user = message.from_user
    args = command.args
    referrer_id = int(args) if args and args.isdigit() and int(args) != user.id else None

    is_new = await create_user(user.id, user.username, user.full_name, referrer_id)

    if is_new and referrer_id:
        referrer = await get_user(referrer_id)
        if referrer:
            await increment_referral(referrer_id)
            updated_referrer = await get_user(referrer_id)
            curr_points = updated_referrer['referrals']
            try:
                await bot.send_message(
                    chat_id=referrer_id,
                    text=(
                        f"🎉 <b>New Referral!</b>\n"
                        f"{html.bold(user.full_name)} joined using your link.\n"
                        f"Your Points: <b>{curr_points}/5</b>"
                    )
                )
            except Exception as e:
                print(f"Could not notify referrer: {e}")

    await show_dashboard(message, user)


async def show_dashboard(message: Message, user):
    user_data = await get_user(user.id)
    points = user_data['referrals'] if user_data else 0
    redeemed = user_data['redeemed'] if user_data else 0
    username = (await message.bot.get_me()).username
    invite_link = f"https://t.me/{username}?start={user.id}"

    if redeemed:
        welcome_text = (
            f"Namaste {html.bold(user.full_name)}! 👋\n\n"
            f"✅ <b>Aapne pehle Redeem kar liya hai!</b>\n"
            f"Admin se contact karein: {OWNER_USERNAME}"
        )
        await message.answer(text=welcome_text)
        return

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

    try:
        await message.answer_photo(photo=NETFLIX_LOGO, caption=welcome_text, reply_markup=keyboard)
    except:
        await message.answer(text=welcome_text, reply_markup=keyboard)


@router.callback_query(F.data == "check_points")
async def check_stats(callback: CallbackQuery):
    await callback.answer("Refreshing...")
    try:
        await callback.message.delete()
    except:
        pass
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

    # Server-side security check
    user_data = await get_user(user.id)
    if not user_data or user_data['referrals'] < 5:
        return await redeem_locked(callback)

    if user_data.get('redeemed'):
        await callback.answer("✅ Aapne pehle hi redeem kar liya hai!", show_alert=True)
        return

    # Mark as redeemed in DB (prevents double redeem)
    await mark_redeemed(user.id)

    # ✅ Notify Admin
    recipient = OWNER_ID if OWNER_ID else OWNER_USERNAME
    admin_msg = (
        f"🚨 <b>NEW REDEEM REQUEST!</b> 🚨\n\n"
        f"👤 <b>User:</b> {user.full_name}\n"
        f"📛 <b>Username:</b> @{user.username}\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"🏆 <b>Referrals:</b> {user_data['referrals']}/5\n\n"
        f"➡️ Contact them at: @{user.username}"
    )
    try:
        await bot.send_message(chat_id=recipient, text=admin_msg)
    except Exception as e:
        print(f"Admin notify failed: {e}")

    # ✅ Update user message
    await callback.message.edit_caption(
        caption=(
            "✅ <b>Request Sent Successfully!</b>\n\n"
            f"Admin ({OWNER_USERNAME}) kuch der mein aapse contact karega.\n"
            "Thoda wait karo! 🎁"
        ),
        reply_markup=None
    )


# ==================== WEB SERVER (RENDER) ====================

async def health(request):
    return web.Response(text="Bot Alive ✅")


async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    # Init DB
    await init_db()
    print("✅ Database initialized.")

    # Start web server for Render port binding
    app = web.Application()
    app.add_routes([web.get('/', health)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"✅ Web server started on port {port}")

    # Delete old webhook & Start polling
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Webhook deleted. Starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
