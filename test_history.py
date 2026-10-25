import io
import json
import unittest
from decimal import Decimal
from unittest.mock import patch
from api.history import handler
from api.telegram import response_for
from history_store import HistoryUnavailable, command, key, save


class HistoryTests(unittest.TestCase):
    def request(self, method, token='a' * 64, payload=None):
        body = json.dumps(payload or {}).encode()
        instance = object.__new__(handler)
        instance.headers = {'Authorization': 'Bearer ' + token, 'Content-Length': str(len(body))}
        instance.rfile = io.BytesIO(body)
        received = []
        instance.respond = lambda status, data: received.append((status, data))
        instance.handle_request(method)
        return received[0]

    @patch('api.history.save')
    def test_server_recalculates_instead_of_trusting_client_total(self, save_mock):
        save_mock.return_value = {'id': 'test'}
        status, _ = self.request('POST', payload={
            'id': '12345678-1234-1234-1234-123456789abc', 'price': '1000',
            'percentage': '40', 'total': '1', 'profit': '999999'})
        self.assertEqual(status, 200)
        args = save_mock.call_args.args
        self.assertEqual(args[0], 'web:' + 'a' * 64)
        self.assertEqual(args[3:5], (Decimal('1400.00'), Decimal('400.00')))

    @patch('api.history.list_history', return_value=[])
    def test_device_isolation_and_auth(self, read):
        self.assertEqual(self.request('GET', token='guess')[0], 401)
        read.assert_not_called()
        self.request('GET', token='a' * 64)
        first = read.call_args.args[0]
        self.request('GET', token='b' * 64)
        self.assertNotEqual(first, read.call_args.args[0])
        self.assertNotEqual(key(first), key('telegram:1'))

    @patch('api.history.save')
    def test_invalid_input_never_saved(self, save_mock):
        for price in ('-1', 'NaN', '0', '1.001'):
            self.assertEqual(self.request('POST', payload={
                'id': '12345678-1234-1234-1234-123456789abc', 'price': price, 'percentage': '40'})[0], 400)
        save_mock.assert_not_called()

    @patch('api.history.list_history', side_effect=HistoryUnavailable())
    def test_database_failure_is_explicit(self, read):
        self.assertEqual(self.request('GET')[0], 503)

    @patch('api.history.clear')
    def test_delete_only_uses_authenticated_owner(self, delete):
        self.assertEqual(self.request('DELETE')[0], 200)
        delete.assert_called_once_with('web:' + 'a' * 64)

    @patch('history_store.command', return_value=1)
    def test_storage_retention_and_retry_key(self, execute):
        save('telegram:1', Decimal('1000'), Decimal('40'), Decimal('1400'), Decimal('400'), 'update-123')
        first = execute.call_args.args
        save('telegram:1', Decimal('1000'), Decimal('40'), Decimal('1400'), Decimal('400'), 'update-123')
        self.assertEqual(first[4], execute.call_args.args[4])
        self.assertIn("'NX'", first[1])
        self.assertIn("'LTRIM', KEYS[1], 0, 99", first[1])
        record = json.loads(first[5])
        self.assertEqual(record['profit'], '400')

    @patch('api.telegram.save', side_effect=HistoryUnavailable())
    def test_telegram_keeps_result_when_database_fails(self, save_mock):
        reply = response_for({'update_id': 1, 'callback_query': {'from': {'id': 1}, 'data': 'calc:1000:40',
            'message': {'chat': {'id': 1, 'type': 'private'}}}}, '123', persist=True)
        self.assertIn('New price: 1,400.00', reply['text'])
        self.assertIn('not saved', reply['text'])

    @patch.dict('os.environ', {'UPSTASH_REDIS_REST_URL': '', 'UPSTASH_REDIS_REST_TOKEN': ''})
    def test_no_database_config_does_not_claim_success(self):
        with self.assertRaises(HistoryUnavailable):
            command('PING')


if __name__ == '__main__':
    unittest.main()
