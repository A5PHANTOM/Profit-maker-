"""Stateless Telegram webhook: price travels in buttons and reply prompts."""
import hmac
import json
import os
import re
from http.server import BaseHTTPRequestHandler

from bot import calculate, number


def buttons(price):
    return {"inline_keyboard": [[
        {"text": f"{percent}%", "callback_data": f"calc:{price}:{percent}"}
        for percent in (30, 40, 50)
    ], [{"text": "Other %", "callback_data": f"custom:{price}"},
        {"text": "New price", "callback_data": "new"}]]}


def response_for(update, bot_id):
    callback = update.get("callback_query")
    message = (callback or {}).get("message") if callback else update.get("message")
    if not message or message.get("chat", {}).get("type") != "private":
        return None
    chat_id = message["chat"]["id"]
    if callback and callback.get("from", {}).get("id") != chat_id:
        return None
    result = {"method": "sendMessage", "chat_id": chat_id}
    text = message.get("text", "").strip()
    try:
        if callback:
            data = callback.get("data", "")
            if data == "new":
                result["text"] = "Send a new original price, for example 1000."
                return result
            parts = data.split(":")
            if len(parts) not in (2, 3):
                return None
            price = number(parts[1])
            if parts[0] == "custom":
                result.update(text=f"Original price: {price}\nReply to this message with your percentage, for example 12.5%.",
                              reply_markup={"force_reply": True, "input_field_placeholder": "Enter percentage"})
                return result
            if parts[0] != "calc" or len(parts) != 3:
                return None
            percent = number(parts[2], percentage=True)
        elif text.split("@", 1)[0].lower() in ("/start", "/help", "/cancel"):
            result["text"] = "Send your original price, then choose 30%, 40%, 50%, or Other %. Profit is the amount added, before fees and taxes."
            return result
        else:
            parent = message.get("reply_to_message", {})
            match = re.fullmatch(r"Original price: ([\d.]+)\nReply to this message with your percentage, for example 12\.5%\.", parent.get("text", ""))
            if match and str(parent.get("from", {}).get("id")) == bot_id:
                price = number(match.group(1))
                try:
                    percent = number(text, percentage=True)
                except ValueError:
                    result.update(text=parent["text"], reply_markup={"force_reply": True})
                    return result
            else:
                price = number(text)
                result.update(text=f"Original price: {price:,.2f}\nChoose the percentage to add.", reply_markup=buttons(price))
                return result
        total, profit = calculate(price, percent)
        result.update(text=f"Original price: {price:,.2f}\nPercentage added: {percent.normalize():f}%\nNew price: {total:,.2f}\nProfit: {profit:,.2f}", reply_markup=buttons(price))
    except (ValueError, IndexError):
        result["text"] = "Enter a valid price, for example 1000. For a custom percentage, reply directly to the percentage prompt."
    return result


class handler(BaseHTTPRequestHandler):
    def respond(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")
        if not token or not secret:
            return self.respond(503, {"error": "Bot environment not configured"})
        supplied = self.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not hmac.compare_digest(supplied.encode(), secret.encode()):
            return self.respond(403, {"error": "Forbidden"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 1000000:
                return self.respond(413, {"error": "Invalid payload size"})
            update = json.loads(self.rfile.read(size))
            if not isinstance(update, dict):
                raise ValueError()
            reply = response_for(update, token.split(":", 1)[0])
        except (ValueError, TypeError, KeyError, AttributeError):
            return self.respond(400, {"error": "Invalid update"})
        self.respond(200, reply or {"ok": True})

    def do_GET(self):
        self.respond(200, {"ok": True, "service": "Telegram calculator webhook"})
