import unittest
from decimal import Decimal

from bot import CalculatorBot, calculate, number


class CalculatorTests(unittest.TestCase):
    def test_markup_and_rounding(self):
        for percent in ("30", "40", "50", "12.5", "0"):
            total, profit = calculate(Decimal("1000"), Decimal(percent))
            self.assertEqual(profit, Decimal("10") * Decimal(percent))
            self.assertEqual(total, Decimal("1000") + profit)
        self.assertEqual(calculate(Decimal("0.05"), Decimal("50")),
                         (Decimal("0.08"), Decimal("0.03")))

    def test_input(self):
        self.assertEqual(number("1,250.50"), Decimal("1250.50"))
        self.assertEqual(number("12.5%", True), Decimal("12.5"))
        for value in ("NaN", "Infinity", "-1", "0", "1,2", "1e10", "0.001", "hello"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                number(value)

    def test_conversation_and_isolation(self):
        sent = []
        bot = CalculatorBot(lambda method, **data: sent.append(data))

        def send(text, user=1):
            bot.handle({"message": {"chat": {"id": user, "type": "private"}, "text": text}})
            return sent[-1]["text"]

        send("/start")
        send("1000")
        self.assertIn("New price: 1,400.00", send("40%"))
        self.assertIn("Profit: 300.00", send("30%"))
        send("Other %")
        self.assertIn("Profit: 125.00", send("12.5"))
        send("200", user=2)
        self.assertIn("Profit: 100.00", send("50%", user=2))
        self.assertIn("Original price: 1,000.00", send("50%"))
        send("New price")
        self.assertNotIn(1, bot.prices)
        send("invalid")
        self.assertNotIn(1, bot.prices)


if __name__ == "__main__":
    unittest.main()
