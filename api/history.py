"""Browser history authenticated by a random device-specific bearer secret."""
import json
import re
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Vercel may load the entrypoint without adding the project root to sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bot import number, calculate
from history_store import save, list_history, clear, HistoryUnavailable


class handler(BaseHTTPRequestHandler):
    def respond(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def handle_request(self, method):
        auth = self.headers.get('Authorization', '')
        if not re.fullmatch(r'Bearer [a-f0-9]{64}', auth):
            return self.respond(401, {'error': 'A valid device key is required.'})
        owner = 'web:' + auth[7:]
        try:
            if method == 'GET':
                return self.respond(200, {'history': list_history(owner)})
            if method == 'DELETE':
                clear(owner)
                return self.respond(200, {'ok': True})
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size < 4096:
                return self.respond(400, {'error': 'Invalid request size.'})
            data = json.loads(self.rfile.read(size))
            price = number(str(data['price']))
            percent = number(str(data['percentage']), percentage=True)
            event = data['id']
            if not isinstance(event, str) or not re.fullmatch(r'[a-zA-Z0-9-]{16,64}', event):
                raise ValueError()
            total, profit = calculate(price, percent)
            record = save(owner, price, percent, total, profit, event)
            return self.respond(200, {'record': record})
        except HistoryUnavailable:
            return self.respond(503, {'error': 'History database unavailable. Check the database environment variables or try again.'})
        except (ValueError, KeyError, TypeError):
            return self.respond(400, {'error': 'Enter a valid price and percentage.'})

    def do_GET(self):
        self.handle_request('GET')

    def do_POST(self):
        self.handle_request('POST')

    def do_DELETE(self):
        self.handle_request('DELETE')
