import unittest
from unittest.mock import patch
from decimal import Decimal
import history_store
from postgres_history import database_url


class PostgresTests(unittest.TestCase):
    @patch.dict('os.environ', {'DATABASE_URL': '', 'bearittprofit_POSTGRES_URL':
        'postgres://test:fake@example.com:6543/postgres?sslmode=require&supa=base-pooler.x&pgbouncer=true'})
    def test_integration_url_removes_non_postgres_parameters(self):
        self.assertEqual(database_url(), 'postgres://test:fake@example.com:6543/postgres?sslmode=require')

    @patch('postgres_history.database_url', return_value='configured')
    @patch('postgres_history.save_record')
    @patch('history_store.command')
    def test_supabase_preferred_to_redis(self, redis, save, url):
        save.return_value = {'id': 'event'}
        result = history_store.save('web:secret', Decimal('1000'), Decimal('40'),
                                    Decimal('1400'), Decimal('400'), 'event')
        self.assertEqual(result['id'], 'event')
        self.assertNotIn('secret', save.call_args.args[0])
        self.assertEqual(save.call_args.args[1]['profit'], '400')
        redis.assert_not_called()

    @patch('postgres_history.database_url', return_value='configured')
    @patch('postgres_history.list_records', return_value=[])
    @patch('postgres_history.clear_records')
    def test_read_and_clear_are_scoped(self, clear, read, url):
        history_store.list_history('web:one')
        history_store.clear('web:two')
        self.assertNotEqual(read.call_args.args[0], clear.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
