"""
tests/test_validators.py
Run:  python -m pytest tests/test_validators.py -v
"""
import sys, os, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.core.validators import (
    validate_symbol, validate_side, validate_order_type,
    validate_quantity, validate_price, validate_all,
)


class TestSymbol(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate_symbol("BTCUSDT"),  "BTCUSDT")
        self.assertEqual(validate_symbol("ethusdt"),  "ETHUSDT")   # lowercase ok
        self.assertEqual(validate_symbol(" SOLUSDT"), "SOLUSDT")   # strips whitespace

    def test_invalid(self):
        for bad in ["BTC", "BTCBUSD", "", "BTC-USDT", "123USDT"]:
            with self.assertRaises(ValueError, msg=f"should reject '{bad}'"):
                validate_symbol(bad)


class TestSide(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate_side("buy"),  "BUY")
        self.assertEqual(validate_side("SELL"), "SELL")

    def test_invalid(self):
        for bad in ["LONG", "SHORT", "", "b"]:
            with self.assertRaises(ValueError):
                validate_side(bad)


class TestOrderType(unittest.TestCase):
    def test_valid(self):
        for t in ["MARKET", "LIMIT", "STOP_MARKET", "market", "limit"]:
            self.assertIn(validate_order_type(t), {"MARKET", "LIMIT", "STOP_MARKET"})

    def test_invalid(self):
        for bad in ["OCO", "TWAP", "FOK", ""]:
            with self.assertRaises(ValueError):
                validate_order_type(bad)


class TestQuantity(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate_quantity("0.001"), "0.001")
        self.assertEqual(validate_quantity("10"),    "10")

    def test_invalid(self):
        for bad in ["0", "-1", "abc", ""]:
            with self.assertRaises(ValueError):
                validate_quantity(bad)


class TestPrice(unittest.TestCase):
    def test_limit_needs_price(self):
        self.assertEqual(validate_price("97000", "LIMIT"), "97000")
        for bad in [None, "", "0", "-5"]:
            with self.assertRaises(ValueError):
                validate_price(bad, "LIMIT")

    def test_stop_market_needs_price(self):
        self.assertEqual(validate_price("58000", "STOP_MARKET"), "58000")
        with self.assertRaises(ValueError):
            validate_price(None, "STOP_MARKET")

    def test_market_ignores_price(self):
        self.assertIsNone(validate_price(None,    "MARKET"))
        self.assertIsNone(validate_price("97000", "MARKET"))


class TestValidateAll(unittest.TestCase):
    def test_market_ok(self):
        r = validate_all("BTCUSDT", "BUY", "MARKET", "0.001")
        self.assertEqual(r["symbol"],     "BTCUSDT")
        self.assertEqual(r["side"],       "BUY")
        self.assertEqual(r["order_type"], "MARKET")
        self.assertIsNone(r["price"])

    def test_limit_ok(self):
        r = validate_all("ETHUSDT", "SELL", "LIMIT", "0.01", "3200")
        self.assertEqual(r["price"], "3200")

    def test_stop_market_ok(self):
        r = validate_all("BTCUSDT", "SELL", "STOP_MARKET", "0.001", "58000")
        self.assertEqual(r["price"], "58000")

    def test_limit_missing_price_raises(self):
        with self.assertRaises(ValueError):
            validate_all("BTCUSDT", "BUY", "LIMIT", "0.001")

    def test_bad_symbol_raises(self):
        with self.assertRaises(ValueError):
            validate_all("BTCBUSD", "BUY", "MARKET", "0.001")


if __name__ == "__main__":
    unittest.main(verbosity=2)
