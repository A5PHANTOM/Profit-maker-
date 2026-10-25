"""A dependency-free Telegram markup calculator. Run with Python 3.10+."""

import json
import logging
import os
import re
import time
from decimal import Decimal, ROUND_HALF_UP
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from pathlib import Path


def load_env():
    """Load the local, git-ignored .env without replacing hosting variables."""
    path = Path(__file__).resolve().parent / ".env"
    if path.is_file():
        for line in path.read_text().splitlines():
            key, separator, value = line.partition("=")
            if separator and key.strip() in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_WEBHOOK_SECRET"):
                os.environ.setdefault(key.strip(), value.strip())


KEYBOARD = {"keyboard": [["30%", "40%", "50%"], ["Other %", "New price"]],
            "resize_keyboard": True}
REMOVE_KEYBOARD = {"remove_keyboard": True}


def number(text, percentage=False):
    value = text.strip()
    if percentage and value.endswith("%"):
        value = value[:-1].strip()
    if len(value) > 32 or not re.fullmatch(r"(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,4})?", value):
        raise ValueError("Enter a positive number, for example 1000 or 1,250.50.")
    result = Decimal(value.replace(",", ""))
    maximum = Decimal("1000000") if percentage else Decimal("1000000000000")
    if result < 0 or result > maximum or (not percentage and result == 0):
        raise ValueError("Percentage must be 0–1,000,000." if percentage else
                         "Price must be greater than 0 and at most 1,000,000,000,000.")
    if not percentage and result.as_tuple().exponent < -2:
        raise ValueError("Enter a price with at most two decimal places.")
    return result


def calculate(price, percent):
    profit = (price * percent / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return price + profit, profit


class CalculatorBot:
    def __init__(self, api):
        self.api = api
        self.prices = {}

    def handle(self, update):
        message = update.get("message", {})
        if not message or message.get("from", {}).get("is_bot"):
            return
        chat = message["chat"]
        chat_id = chat["id"]
        # Each conversation is private, so a price always belongs to its sender.
        if chat.get("type") != "private":
            self.api("sendMessage", chat_id=chat_id, text="Open a private chat with me to calculate prices.")
            return
        text = message.get("text", "").strip()
        command = text.split("@", 1)[0].lower()
        reply = {"chat_id": chat_id}
        if command in ("/start", "/help", "/cancel") or text.lower() == "new price":
            self.prices.pop(chat_id, None)
            reply.update(text="Send the original price (for example 1000). Then choose 30%, 40%, 50%, or Other %.\n\nI add the percentage to your original price. Profit is the added amount, before any other costs.", reply_markup=REMOVE_KEYBOARD)
        elif chat_id not in self.prices:
            try:
                price = number(text)
                self.prices[chat_id] = price
                reply.update(text=f"Original price: {price:,.2f}\nChoose a percentage below, or type your own (for example 25%).", reply_markup=KEYBOARD)
            except ValueError as error:
                reply.update(text=str(error), reply_markup=REMOVE_KEYBOARD)
        elif text.lower() == "other %":
            reply.update(text="Enter your percentage, for example 12.5 or 12.5%.", reply_markup=KEYBOARD)
        else:
            try:
                percent = number(text, percentage=True)
                price = self.prices[chat_id]
                total, profit = calculate(price, percent)
                reply.update(text=f"Original price: {price:,.2f}\nPercentage added: {percent.normalize():f}%\nNew price: {total:,.2f}\nProfit: {profit:,.2f}\n\nChoose another percentage to compare, or tap New price.", reply_markup=KEYBOARD)
            except ValueError as error:
                reply.update(text=f"{error}\nChoose a percentage or tap New price.", reply_markup=KEYBOARD)
        self.api("sendMessage", **reply)


class TelegramError(Exception):
    def __init__(self, code, retry_after=5):
        self.code = code
        self.retry_after = retry_after
        super().__init__(f"Telegram API error {code}")


def telegram_api(token):
    def call(method, **data):
        request = Request(f"https://api.telegram.org/bot{token}/{method}",
                          data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=40) as response:
                result = json.load(response)
        except HTTPError as error:
            try:
                body = json.loads(error.read())
            except (ValueError, OSError):
                body = {}
            raise TelegramError(error.code, body.get("parameters", {}).get("retry_after", 5)) from None
        if not result.get("ok"):
            raise TelegramError(result.get("error_code", 500), result.get("parameters", {}).get("retry_after", 5))
        return result["result"]
    return call


def main():
    load_env()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN to the token from @BotFather, then run python3 bot.py.")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    api = telegram_api(token)
    bot = CalculatorBot(api)
    offset = 0
    try:
        identity = api("getMe")
        logging.info("Bot @%s is running. Press Ctrl+C to stop.", identity["username"])
        while True:
            try:
                updates = api("getUpdates", offset=offset, timeout=30, allowed_updates=["message"])
                for update in updates:
                    try:
                        bot.handle(update)
                    except TelegramError as error:
                        if error.code not in (400, 403):
                            raise
                        logging.warning("Could not reply to a message (API %s).", error.code)
                    offset = update["update_id"] + 1
            except TelegramError as error:
                if error.code in (401, 404, 409):
                    raise
                logging.warning("Telegram temporarily unavailable (API %s); retrying.", error.code)
                time.sleep(max(1, error.retry_after))
            except (URLError, TimeoutError, OSError):
                logging.warning("Network unavailable; retrying in 5 seconds.")
                time.sleep(5)
    except KeyboardInterrupt:
        logging.info("Stopped.")
    except TelegramError as error:
        raise SystemExit(f"Telegram API error {error.code}. Check your token; for 409, stop other bot instances and remove any webhook.") from None


if __name__ == "__main__":
    main()
