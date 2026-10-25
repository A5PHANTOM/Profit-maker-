"""Verify live persistence and isolation using temporary, isolated test owners."""
import sys
import uuid
from pathlib import Path
from decimal import Decimal
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bot import load_env
from history_store import save, list_history, clear, HistoryUnavailable
from postgres_history import connection


def check():
    load_env()
    owners = ['verification:' + str(uuid.uuid4()) for _ in range(2)]
    try:
        for owner in owners:
            save(owner, Decimal('1000'), Decimal('40'), Decimal('1400'), Decimal('400'), 'test-event')
        save(owners[0], Decimal('1000'), Decimal('40'), Decimal('1400'), Decimal('400'), 'test-event')
        rows = list_history(owners[0])
        assert len(rows) == 1 and rows[0]['profit'] == '400'
        clear(owners[0])
        assert not list_history(owners[0])
        assert len(list_history(owners[1])) == 1
        with connection() as conn:
            for role in ('anon', 'authenticated'):
                assert not conn.execute('SELECT has_schema_privilege(%s, %s, %s)',
                                        (role, 'profit_private', 'USAGE')).fetchone()[0]
        print('Live Supabase checks passed: save, read, retry deduplication, owner isolation, deletion, and public-role restrictions.')
    finally:
        for owner in owners:
            clear(owner)


if __name__ == '__main__':
    try:
        check()
    except HistoryUnavailable:
        raise SystemExit('Live database check failed: database unavailable. No credentials were printed.') from None
