# Telegram price and profit bot

## Database and history

History now uses **Supabase Postgres** when `bearittprofit_POSTGRES_URL` (from your Vercel Supabase integration) or `DATABASE_URL` is set. Credentials are read only by Python server code. No Supabase secret keys are required in the browser.

1. Connect your Supabase integration to this Vercel project and enable its variables for Production.
2. Install Python dependencies: `python3 -m pip install -r requirements.txt` (prefer a virtual environment).
3. With the Postgres connection URL in the ignored `.env`, run `python3 scripts/init_db.py` once. It creates only the `profit_private` schema, history table, and index. Public API roles have no access; browser access goes through `/api/history` and its private device key.
4. Redeploy Vercel. Both Telegram `/history` and the web history panel use this database.

To inspect saved rows in Supabase SQL Editor, use `SELECT record FROM profit_private.calculation_history ORDER BY sequence DESC LIMIT 100;`. Run `python3 scripts/check_db.py` to verify real saves, reads, isolation, deletion, and API-role restrictions using temporary records. This test cleans up its own records.

Amounts are stored as exact decimal strings inside JSONB records. Saves use transactions, per-owner locks, and unique event IDs to prevent duplicate retained records. The latest 100 records per browser/chat are retained. Clearing browser history deletes that browser's rows. See `migrations/001_history.sql` for the schema; it can also be run through Supabase SQL Editor.

The previous Upstash backend is still supported when no Postgres URL is configured. To use it, set:

```text
UPSTASH_REDIS_REST_URL=https://your-database.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-rest-token
```

For Upstash only, use a REST token with write access; no SQL migration is required. Redeploy after adding variables. Database requests use the [Upstash REST API](https://upstash.com/docs/redis/features/restapi).

The website saves when you tap **Calculate**, or choose a preset after calculating. View **Your history** below the result, **Refresh** it, or **Clear** it. Typing updates the preview; tap Calculate to save that preview. Offline calculations still work; offline entries are not queued or saved. Failed saves display an explicit message. History is not cached by the service worker.

Web history is private to a random browser key stored on your device. There is no account sign-in or cross-device sync: clearing browser data loses access to that history. Safari and the installed app may have separate storage. Treat the browser key as a credential. Telegram history is separate and scoped to the Telegram private chat: send **/history** to see your latest 10 calculations. Both webhook and local polling save to the same Telegram history.

The database retains the latest **100 calculations per browser/chat**, with amounts, percentage and UTC timestamp. Server-side code recalculates submitted values. Postgres deduplicates events while they are retained; Upstash deduplicates them for 7 days. The database must be configured for saving to work; calculations remain available when it is not.

For full local API development use `vercel dev`; the simple static HTTP server can preview the calculator but cannot provide database endpoints. Run `python3 -m unittest -v`, `node test_web.cjs`, and `node test_offline.cjs` for checks.

## Web version — deploy on Vercel

### iPhone app

The website is an installable web app, with a compact iPhone layout, decimal keypad, large touch controls, safe-area support, and an app icon. It is not an App Store / native iOS build.

After deploying, open the HTTPS Vercel URL in **Safari**, tap **Share → Add to Home Screen**, keep **Open as Web App** enabled if shown, and tap **Add**. Launch it from the new icon for the standalone app experience. Wait for **Ready to use offline** on the first visit before trying airplane mode. Browser storage eviction or clearing site data can remove offline availability.

The current form resets when the page reloads; saved history remains in the database. No account is required. Fonts are built in, so there are no external font requests. To release app changes, update the cache version in `public/sw.js`; close all app windows and reopen after the update has downloaded to activate the new version. Icon source: `scripts/make_icons.py`.

The responsive browser calculator is in `public/`. It includes 30%, 40%, 50%, custom percentages, live updates after your first calculation, and a reset button. Basic calculations need no backend or Telegram token. Saving and viewing history requires the database environment variables above and `/api/history` on Vercel.

1. Push this folder to a GitHub repository.
2. In Vercel, choose **Add New → Project**, then import that repository.
3. Choose framework preset **Other**, leave the build command empty, and use output directory **public** (also configured in `vercel.json`).
4. Click **Deploy**.

To preview locally, run `python3 -m http.server 8000 --directory public` and visit `http://localhost:8000`. To check the web calculation logic, run `node test_web.cjs`.

### Telegram bot on Vercel

The repository also includes `/api/telegram`, a Python webhook that runs on Vercel. It keeps the original price inside Telegram buttons and custom-percentage reply prompts, so the active conversation survives server restarts. History uses the database configured above.

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

   This prompt works in macOS's default zsh. The token stays hidden while you paste. Keep it private. Alternatively, save the token in the ignored `.env` file; the bot loads it automatically. Environment variables take precedence.

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
