"""Create the private history schema using the server-only database URL."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bot import load_env
from postgres_history import connection
from history_store import HistoryUnavailable

if __name__ == '__main__':
    load_env()
    try:
        with connection() as conn:
            conn.execute((Path(__file__).resolve().parents[1] / 'migrations/001_history.sql').read_text(), prepare=False)
    except HistoryUnavailable:
        raise SystemExit('Database initialization failed. Check database URL, password, network and project status.') from None
    print('Supabase connected. Private history table and index created.')
