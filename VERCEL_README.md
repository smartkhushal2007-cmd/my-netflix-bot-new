# ⚡ Deploying on Vercel

Since Railway is paid, here is how you can deploy for **Free on Vercel**.

## ⚠️ Important Limitations
1.  **Database**: Vercel deletes files after running. Your database (`giveaway_bot.db`) will **RESET** every time the bot sleeps (every few minutes).
    *   I have added a `VERCEL` mode that keeps data in "Memory" (RAM). This also resets often.
    *   **Solution**: For a real giveaway, you should use a real database (like MongoDB Atlas or Supabase) or just use **Render.com** (it has a free tier for web services).
2.  **Webhooks**: Vercel does not use "polling" (running inside a loop). It waits for Telegram to *send* the message to Vercel.

---

## 🚀 Steps to Deploy

### 1. Create Github Repo
1.  Go to `github.com/new` and create a repository (e.g., `giveaway-bot`).
2.  Upload all these files (`bot.py`, `vercel.json`, `api/webhook.py`, `requirements.txt`) to the repo.

### 2. Connect to Vercel
1.  Go to `vercel.com` -> **Add New** -> **Project**.
2.  Import your GitHub repository.
3.  **Environment Variables**:
    Add a new variable:
    *   Name: `VERCEL`
    *   Value: `1`
    (This tells the bot to use Memory Database instead of trying to write to a readonly file).
4.  Click **Deploy**.

### 3. Set the Webhook (CRITICAL)
Once deployed, Vercel will give you a domain like `https://giveaway-bot.vercel.app`.
You need to tell Telegram to send messages there.

Open your browser and visit:
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://<YOUR_VERCEL_DOMAIN>/webhook
```
Replace:
*   `<YOUR_BOT_TOKEN>` with your actual token.
*   `<YOUR_VERCEL_DOMAIN>` with the domain Vercel gave you.

If successful, you will see `Webhook was set`.

### 4. Test
Send `/start` to your bot. It should reply!
