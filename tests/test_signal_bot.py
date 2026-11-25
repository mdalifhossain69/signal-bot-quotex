"""Unit tests for the signal bot (stdlib unittest)."""

from __future__ import annotations

import json
import unittest

from signal_bot.config import Config
from signal_bot.risk import RiskManager
from signal_bot.signals import Signal, SignalError, is_valid, parse, parse_json, parse_text
from signal_bot.trader import Trader


class TestSignalParsing(unittest.TestCase):
    def test_text_buy(self):
        sig = parse_text("BUY EURUSD 5m")
        self.assertEqual(sig.action, "buy")
        self.assertEqual(sig.symbol, "EURUSD")
        self.assertEqual(sig.duration, 5)
        self.assertEqual(sig.duration_unit, "m")

    def test_text_aliases(self):
        self.assertEqual(parse_text("call GBPUSD 5M").action, "buy")
        self.assertEqual(parse_text("PUT USDJPY 1").action, "sell")
        self.assertEqual(parse_text("down AUDUSD 2s").action, "sell")
        self.assertEqual(parse_text("bull XAUUSD 3m").action, "buy")

    def test_text_defaults(self):
        sig = parse_text("sell EURUSD")
        self.assertEqual(sig.duration, 5)
        self.assertEqual(sig.duration_unit, "m")

    def test_json_signal(self):
        sig = parse_json('{"action": "BUY", "symbol": "EURUSD", "duration": 5, "duration_unit": "m"}')
        self.assertEqual(sig.action, "buy")
        self.assertEqual(sig.symbol, "EURUSD")
        self.assertEqual(sig.duration, 5)

    def test_json_dict_input(self):
        sig = parse_json({"action": "sell", "symbol": "GBPJPY", "duration": 2})
        self.assertEqual(sig.action, "sell")
        self.assertEqual(sig.symbol, "GBPJPY")
        self.assertEqual(sig.duration, 2)

    def test_auto_detect(self):
        self.assertEqual(parse("BUY EURUSD 5m").action, "buy")
        self.assertEqual(parse('{"action":"sell","symbol":"USDJPY"}').action, "sell")

    def test_empty_signal_raises(self):
        with self.assertRaises(SignalError):
            parse_text("")

    def test_unknown_action_raises(self):
        with self.assertRaises(SignalError):
            parse_text("HOLD EURUSD 5m")

    def test_normalization(self):
        sig = Signal(action="BUY", symbol="eurusd", duration=5, confidence=1.5).normalized()
        self.assertEqual(sig.action, "buy")
        self.assertEqual(sig.symbol, "EURUSD")
        self.assertEqual(sig.confidence, 1.0)

    def test_validation(self):
        good = Signal(action="buy", symbol="EURUSD", duration=5)
        self.assertEqual(is_valid(good), [])
        bad = Signal(action="hold", symbol="BAD", duration=0, confidence=2.0)
        self.assertNotEqual(is_valid(bad), [])


class TestConfig(unittest.TestCase):
    def test_defaults(self):
        cfg = Config.from_env()
        self.assertEqual(cfg.mode, "mock")
        self.assertTrue(cfg.quotex_demo)
        self.assertEqual(cfg.default_amount, 1.0)

    def test_validation_errors(self):
        cfg = Config(mode="bogus", default_amount=-1, min_confidence=2.0)
        errs = cfg.validate()
        self.assertTrue(any("SIGNAL_BOT_MODE" in e for e in errs))
        self.assertTrue(any("AMOUNT" in e for e in errs))
        self.assertTrue(any("MIN_CONFIDENCE" in e for e in errs))

    def test_from_env_override(self):
        import os
        os.environ["SIGNAL_BOT_MODE"] = "real"
        os.environ["DEFAULT_AMOUNT"] = "10"
        cfg = Config.from_env()
        self.assertEqual(cfg.mode, "real")
        self.assertEqual(cfg.default_amount, 10.0)
        del os.environ["SIGNAL_BOT_MODE"]
        del os.environ["DEFAULT_AMOUNT"]


class TestRiskManager(unittest.TestCase):
    def setUp(self):
        self.config = Config(max_daily_loss=10.0, max_concurrent_trades=1)
        self.risk = RiskManager(self.config)

    def test_can_trade(self):
        ok, reason = self.risk.can_trade(Signal(action="buy", symbol="EURUSD", duration=5), 1.0)
        self.assertTrue(ok)
        self.assertIsNone(reason)

    def test_daily_loss_limit(self):
        from signal_bot.risk import TradeResult
        import time
        self.risk.stats.date = time.strftime("%Y-%m-%d")
        self.risk.stats.total_profit = -10.0
        ok, reason = self.risk.can_trade(Signal(action="buy", symbol="EURUSD", duration=5), 1.0)
        self.assertFalse(ok)
        self.assertIn("loss", reason.lower())

    def test_concurrent_limit(self):
        self.risk.open_trade("t1")
        ok, reason = self.risk.can_trade(Signal(action="buy", symbol="EURUSD", duration=5), 1.0)
        self.assertFalse(ok)
        self.assertIn("concurrent", reason.lower())

    def test_record_updates_stats(self):
        from signal_bot.risk import TradeResult
        r = TradeResult(success=True, trade_id="t1", symbol="EURUSD", action="buy",
                        amount=1.0, duration=5, profit=0.8)
        self.risk.record(r)
        self.assertEqual(self.risk.stats.trades, 1)
        self.assertEqual(self.risk.stats.wins, 1)


class TestTrader(unittest.TestCase):
    def test_mock_trade(self):
        config = Config(mode="mock")
        trader = Trader(config)
        self.assertTrue(trader.connect())
        result = trader.place_trade(Signal(action="buy", symbol="EURUSD", duration=5), amount=1.0)
        self.assertTrue(result.success)
        self.assertEqual(result.symbol, "EURUSD")
        self.assertEqual(result.amount, 1.0)
        self.assertIsInstance(result.profit, float)

    def test_real_mode_not_connected(self):
        config = Config(mode="real")
        trader = Trader(config)
        result = trader.place_trade(Signal(action="buy", symbol="EURUSD", duration=5), amount=1.0)
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)


if __name__ == "__main__":
    unittest.main()
