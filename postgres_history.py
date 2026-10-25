"""Server-only Supabase Postgres storage; no credentials sent to the browser."""
import json
import os
from contextlib import contextmanager
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode


def database_url():
    value = os.environ.get('DATABASE_URL') or os.environ.get('bearittprofit_POSTGRES_URL')
    if not value:
        return None
    parts = urlsplit(value)
    query = urlencode([(name, value) for name, value in parse_qsl(parts.query)
                       if name not in ('supa', 'pgbouncer')])
    return urlunsplit(parts._replace(query=query))


@contextmanager
def connection():
    from history_store import HistoryUnavailable
    try:
        import psycopg
        if not database_url():
            raise HistoryUnavailable('Supabase database is not configured')
        # Supabase transaction pooler does not support named prepared statements.
        with psycopg.connect(database_url(), sslmode='require', connect_timeout=10,
                             prepare_threshold=None) as conn:
            conn.execute("SET LOCAL statement_timeout = '10s'")
            yield conn
    except (ImportError, OSError):
        raise HistoryUnavailable('Supabase database unavailable') from None
    except Exception as error:
        if error.__class__.__module__.startswith('psycopg'):
            raise HistoryUnavailable('Supabase database unavailable') from None
        raise


def save_record(owner_hash, record):
    with connection() as conn:
        # Serialize writes/deletes per owner, including concurrent function instances.
        conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))', (owner_hash,))
        conn.execute('INSERT INTO profit_private.calculation_history (owner_hash, event_id, record) '
                     'VALUES (%s, %s, %s::jsonb) ON CONFLICT (owner_hash, event_id) DO NOTHING',
                     (owner_hash, record['id'], json.dumps(record)))
        conn.execute('DELETE FROM profit_private.calculation_history WHERE owner_hash = %s '
                     'AND sequence NOT IN (SELECT sequence FROM profit_private.calculation_history '
                     'WHERE owner_hash = %s ORDER BY sequence DESC LIMIT 100)', (owner_hash, owner_hash))
        return conn.execute('SELECT record FROM profit_private.calculation_history '
                            'WHERE owner_hash = %s AND event_id = %s', (owner_hash, record['id'])).fetchone()[0]


def list_records(owner_hash):
    with connection() as conn:
        return [row[0] for row in conn.execute('SELECT record FROM profit_private.calculation_history '
                    'WHERE owner_hash = %s ORDER BY sequence DESC LIMIT 100', (owner_hash,)).fetchall()]


def clear_records(owner_hash):
    with connection() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))', (owner_hash,))
        conn.execute('DELETE FROM profit_private.calculation_history WHERE owner_hash = %s', (owner_hash,))
