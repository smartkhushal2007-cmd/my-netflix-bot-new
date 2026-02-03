# ☁️ Vercel Deployment Guide

Follow these steps to put your bot online 24/7 for Free.

### Step 1: Upload Logic to GitHub
1.  **Login to GitHub** (If you don't have an account, create one).
2.  **Create New Repository**:
    *   Click the `+` icon -> "New repository".
    *   Name it: `netflix-giveaway-bot`.
    *   Make it **Private** (recommended) or Public.
    *   Click **Create repository**.
3.  **Upload Files**:
    *   Click "uploading an existing file".
    *   Drag and drop ALL files from your bot folder (`bot.py`, `requirements.txt`, `vercel.json`, `api/webhook.py`).
    *   Click **Commit changes**.

### Step 2: Deploy on Vercel
1.  Go to [Vercel.com](https://vercel.com) and Login.
2.  Click **"Add New..."** -> **"Project"**.
3.  You will see your GitHub repo `netflix-giveaway-bot`. Click **Import**.
4.  **Configure Project**:
    *   Scroll down to **Environment Variables**.
    *   Add a new one:
        *   **Key**: `VERCEL`
        *   **Value**: `1`
    *   (No other changes needed).
5.  Click **Deploy**.
6.  Wait ~1 minute. Once done, it will show "Congratulations!".
7.  Click **Continue to Dashboard** and look for your **Domain** (e.g., `netflix-giveaway-bot.vercel.app`). **Copy this link.**

### Step 3: Connect Bot (Critical)
Now tell Telegram to send messages to Vercel.

1.  **Copy this link**:
    ```
    https://api.telegram.org/bot8207872443:AAHxbq29c3zt58N5Rqu_9KgHQyrEyV1l-3o/setWebhook?url=YOUR_VERCEL_DOMAIN/webhook
    ```
2.  **Replace** `YOUR_VERCEL_DOMAIN` with the link you copied from Vercel.
    *   Example: `.../setWebhook?url=https://netflix-giveaway-bot.vercel.app/webhook`
3.  **Paste** the full link in your browser and hit Enter.
4.  You should see: `Webhook was set`.

### 🎉 Done!
Your bot is now live 24/7. You can close your computer/CMD.

### ❓ Troubleshooting
*   **Bot not replying?** Check the webhook link again carefully.
*   **Memory Reset**: Remember, on Vercel, the User Points might reset if the bot "sleeps" (Vercel shuts down inactive functions). For a serious giveaway, you might eventually need a real server or database, but for starting, this works!
