import unittest
from api.telegram import response_for


class WebhookTests(unittest.TestCase):
    def test_stateless_price_and_buttons(self):
        update = {'message': {'chat': {'id': 1, 'type': 'private'}, 'text': '1000'}}
        reply = response_for(update, '123')
        data = reply['reply_markup']['inline_keyboard'][0][1]['callback_data']
        result = response_for({'callback_query': {'from': {'id': 1}, 'data': data,
            'message': {'chat': {'id': 1, 'type': 'private'}}}}, '123')
        self.assertIn('New price: 1,400.00', result['text'])
        self.assertIn('Profit: 400.00', result['text'])

    def test_custom_reply_after_cold_start(self):
        prompt = response_for({'callback_query': {'from': {'id': 1}, 'data': 'custom:1000',
            'message': {'chat': {'id': 1, 'type': 'private'}}}}, '123')
        result = response_for({'message': {'chat': {'id': 1, 'type': 'private'}, 'text': '12.5%',
            'reply_to_message': {'text': prompt['text'], 'from': {'id': 123}}}}, '123')
        self.assertIn('Profit: 125.00', result['text'])

    def test_untrusted_prompt_is_not_percentage_context(self):
        result = response_for({'message': {'chat': {'id': 1, 'type': 'private'}, 'text': '50',
            'reply_to_message': {'text': 'Original price: 1000\nReply to this message with your percentage, for example 12.5%.',
                                 'from': {'id': 999}}}}, '123')
        self.assertIn('Original price: 50.00', result['text'])


if __name__ == '__main__':
    unittest.main()
