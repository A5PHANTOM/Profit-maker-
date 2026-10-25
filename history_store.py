"""Private calculation history in serverless-compatible Upstash Redis."""
import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError


class HistoryUnavailable(Exception):
    pass


def command(*args):
    url = os.environ.get('UPSTASH_REDIS_REST_URL', '').rstrip('/')
    token = os.environ.get('UPSTASH_REDIS_REST_TOKEN', '')
    if not url.startswith('https://') or not token:
        raise HistoryUnavailable('Database not configured')
    request = Request(url, data=json.dumps(args).encode(), headers={
        'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
    try:
        with urlopen(request, timeout=8) as response:
            data = json.load(response)
        if 'error' in data:
            raise HistoryUnavailable('Database request failed')
        return data['result']
    except (URLError, OSError, ValueError, KeyError):
        raise HistoryUnavailable('Database unavailable') from None


def key(owner):
    return 'profit:history:' + hashlib.sha256(owner.encode()).hexdigest()


def save(owner, price, percent, total, profit, event_id=None):
    record = {'id': str(event_id or uuid.uuid4()), 'created_at': datetime.now(timezone.utc).isoformat(),
              'original': str(price), 'percentage': str(percent), 'total': str(total), 'profit': str(profit)}
    # Atomic retry deduplication and bounded retention: latest 100 calculations.
    script = """if redis.call('SET', KEYS[2], '1', 'NX', 'EX', 604800) then
      redis.call('LPUSH', KEYS[1], ARGV[1]); redis.call('LTRIM', KEYS[1], 0, 99); return 1
      end; return 0"""
    event_key = key(owner) + ':event:' + hashlib.sha256(record['id'].encode()).hexdigest()
    command('EVAL', script, 2, key(owner), event_key, json.dumps(record))
    return record


def list_history(owner):
    return [json.loads(row) for row in command('LRANGE', key(owner), 0, 99) or []]


def clear(owner):
    command('DEL', key(owner))


def telegram_history(chat_id):
    try:
        rows = list_history('telegram:' + str(chat_id))[:10]
    except HistoryUnavailable:
        return 'History is unavailable. Configure the database or try again shortly.'
    if not rows:
        return 'No saved calculations yet. Send a price to get started.'
    return 'Your latest calculations (up to 10):\n\n' + '\n\n'.join(
        f"{row['created_at'][:16].replace('T', ' ')} UTC\n"
        f"{row['original']} + {row['percentage']}% = {row['total']} | Profit: {row['profit']}" for row in rows)
