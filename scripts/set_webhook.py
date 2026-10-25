"""Run once after deploying: python3 scripts/set_webhook.py https://your-app.vercel.app"""
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import os
from bot import load_env, telegram_api, TelegramError

if __name__ == '__main__':
    load_env()
    if len(sys.argv) != 2 or urlparse(sys.argv[1]).scheme != 'https' or not urlparse(sys.argv[1]).netloc:
        raise SystemExit('Usage: python3 scripts/set_webhook.py https://your-app.vercel.app')
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    secret = os.environ.get('TELEGRAM_WEBHOOK_SECRET')
    if not token or not secret:
        raise SystemExit('Set TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_SECRET in .env first.')
    try:
        telegram_api(token)('setWebhook', url=sys.argv[1].rstrip('/') + '/api/telegram',
                            secret_token=secret, allowed_updates=['message', 'callback_query'])
    except TelegramError as error:
        raise SystemExit(str(error)) from None
    print('Telegram webhook connected. Stop any local polling bot.')
