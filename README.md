# Telegram price and profit bot

## Web version — deploy on Vercel

### iPhone app

The website is an installable web app, with a compact iPhone layout, decimal keypad, large touch controls, safe-area support, and an app icon. It is not an App Store / native iOS build.

After deploying, open the HTTPS Vercel URL in **Safari**, tap **Share → Add to Home Screen**, keep **Open as Web App** enabled if shown, and tap **Add**. Launch it from the new icon for the standalone app experience. Wait for **Ready to use offline** on the first visit before trying airplane mode. Browser storage eviction or clearing site data can remove offline availability.

Calculation data stays on the device and resets when the page reloads. No account is required. Fonts are built in, so there are no external font requests. To release app changes, update the cache version in `public/sw.js`; close all app windows and reopen after the update has downloaded to activate the new version. Icon source: `scripts/make_icons.py`.

The responsive browser calculator is in `public/`. It includes 30%, 40%, 50%, custom percentages, live updates after your first calculation, and a reset button. No backend, dependencies, environment variables, or Telegram token are needed for the website.

1. Push this folder to a GitHub repository.
2. In Vercel, choose **Add New → Project**, then import that repository.
3. Choose framework preset **Other**, leave the build command empty, and use output directory **public** (also configured in `vercel.json`).
4. Click **Deploy**.

To preview locally, run `python3 -m http.server 8000 --directory public` and visit `http://localhost:8000`. To check the web calculation logic, run `node test_web.cjs`.

### Telegram bot on Vercel

The repository also includes `/api/telegram`, a Python webhook that runs on Vercel. It keeps the original price inside Telegram buttons and custom-percentage reply prompts, so it needs no database and survives server restarts.

1. In Vercel Project Settings → Environment Variables, add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_WEBHOOK_SECRET` from your local `.env`. Select Production (and Preview if required), then deploy/redeploy. The ignored `.env` is never pushed to GitHub or uploaded automatically.
2. Ensure the production URL is publicly reachable by Telegram (no Vercel login protection).
3. Stop the locally running polling bot, then run `python3 scripts/set_webhook.py https://YOUR-PROJECT.vercel.app` from this folder.
4. Open your bot and send `/start`. For Other %, reply directly to the bot's percentage prompt.

Use `python3 bot.py` only for local polling; it now reads `.env` automatically. Telegram supports either polling or a webhook at a time. To go back to polling, remove the webhook first. Keep the `.env` file private; `.env.example` contains placeholders for other checkouts.

Python 3.10+; no packages to install.

## Start

1. Open [@BotFather](https://t.me/BotFather) in Telegram, send `/newbot`, and follow the prompts to get your bot token.
2. In your terminal, inside this folder, run:

   ```sh
   read -s 'TELEGRAM_BOT_TOKEN?Paste bot token: '
   export TELEGRAM_BOT_TOKEN
   python3 bot.py
   ```

   This prompt works in macOS's default zsh. The token stays hidden while you paste. Keep it private. The bot reads the environment variable, not a `.env` file.

3. Open your bot in Telegram and tap **Start**. Send a price, then tap **30%**, **40%**, **50%**, or **Other %**. You can also type a percentage directly.

Example: original price **1,000**, percentage **40%** → new price **1,400.00**, profit **400.00**.

The percentage is a markup on the original price: `profit = price × percentage / 100`, `new price = price + profit`. Profit excludes fees, taxes, and other costs. Amounts use your input currency and round to two decimals (half up). Prices accept up to two decimal places; percentages accept up to four, including 0%.

Choose another percentage to compare using the same original price. Tap **New price** or send `/cancel` to start over. `/help` also restarts the conversation.

The process must keep running on a computer or server for the bot to respond. Run one instance per token; this bot uses Telegram long polling and requires no public web server. Private chats only. Conversation prices are held in memory and reset on restart; send a new price after restarting. A bot previously configured with a webhook must have that webhook removed before polling can run.

## Verify

```sh
python3 -m unittest -v
```

API reference: [Telegram Bot API](https://core.telegram.org/bots/api).
