# Netflix Giveaway Bot

A fully functional Telegram bot built with Python and Aiogram 3.

## Features
- Welcome message with verification flow using Inline Buttons.
- Checks channel membership (requires Bot Admin status in channel).
- User verification for adding members.
- Screenshot upload handling with database logging.
- Forwards screenshots directly to the owner/admin.
- SQLite database to track users and prevent duplicate submissions.
- Admin `/stats` command.

## Prerequisites
- Python 3.8+
- Telegram Bot Token
- A Telegram Channel (where the bot is an Admin)

## Setup & Run

### 1. Install Dependencies
Run the following command to install required libraries:
```bash
pip install -r requirements.txt
```

### 2. Configuration
Open `bot.py` and update the following configuration variables at the top:
- `TOKEN`: Your Bot API Token (Already pre-filled).
- `OWNER_ID`: **IMPORTANT**: Replace `None` with your numeric Telegram ID (integer). This ensures you receive the screenshots. You can find this ID using bots like `@userinfobot`.
- `CHANNEL_USERNAME`: The channel users must join.
- `OWNER_USERNAME`: Fallback username if ID is not set.

### 3. Run the Bot
```bash
python bot.py
```

## Deployment Options

### Replit
1. Create a new Python Rep.
2. Upload `bot.py` and `requirements.txt`.
3. In the Shell, run `pip install -r requirements.txt`.
4. Click "Run" (ensure `.replit` is configured to run `python bot.py`).

### Railway / Heroku
1. Create a GitHub repository with these files.
2. Connect the repo to Railway/Heroku.
3. **Railway**: Simply add the repo; it detects `requirements.txt`. Add a Start Command: `python bot.py`.
4. **Heroku**: Create a `Procfile` containing:
   ```
   worker: python bot.py
   ```
   Then push to Heroku.

## Admin Commands
- `/stats`: View total users and completions (Only works for the Owner).
