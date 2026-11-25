"""Trade execution — mock (simulated) and real Quotex modes."""

from __future__ import annotations

import random
import time
import uuid
from dataclasses import asdict
from typing import Optional

from .config import Config
from .risk import TradeResult
from .signals import Signal


class Trader:
    """Places trades either in mock mode or against the Quotex API."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._connected = False

    def connect(self) -> bool:
        """Establish a connection (real mode only)."""
        if self.config.mode == "mock":
            self._connected = True
            return True
        return self._connect_real()

    def _connect_real(self) -> bool:
        """Connect to Quotex via websocket using SSID or email/password."""
        # The Quotex unofficial API speaks Socket.IO over websocket. A full
        # implementation is out of scope here; this is the integration point.
        if self.config.quotex_ssid:
            # Would authenticate with ssid via websocket
            pass
        elif self.config.quotex_email and self.config.quotex_password:
            # Would authorize via email/password then use returned ssid
            pass
        else:
            return False
        self._connected = True
        return True

    def is_connected(self) -> bool:
        return self._connected

    def place_trade(
        self,
        signal: Signal,
        amount: Optional[float] = None,
        duration: Optional[int] = None,
    ) -> TradeResult:
        """Place a trade and return its result."""
        amount = amount if amount is not None else self.config.default_amount
        duration = duration if duration is not None else signal.duration

        if self.config.mode == "mock":
            return self._place_mock_trade(signal, amount, duration)
        return self._place_real_trade(signal, amount, duration)

    def _place_mock_trade(self, signal: Signal, amount: float, duration: int) -> TradeResult:
        """Simulate a trade outcome (win probability ~55%)."""
        trade_id = f"mock-{uuid.uuid4().hex[:12]}"
        win = random.random() < 0.55
        payout = 0.80  # typical 80% payout
        profit = round(amount * payout, 2) if win else -round(amount, 2)
        return TradeResult(
            success=True,
            trade_id=trade_id,
            symbol=signal.symbol,
            action=signal.action,
            amount=amount,
            duration=duration,
            profit=profit,
        )

    def _place_real_trade(self, signal: Signal, amount: float, duration: int) -> TradeResult:
        """Place a real trade on Quotex (stub)."""
        if not self._connected:
            return TradeResult(
                success=False,
                trade_id="",
                symbol=signal.symbol,
                action=signal.action,
                amount=amount,
                duration=duration,
                error="not connected to Quotex",
            )
        # Real implementation would open a digital option via websocket here,
        # e.g. send a "buy" message and wait for the trade id / result.
        trade_id = f"qx-{uuid.uuid4().hex[:12]}"
        return TradeResult(
            success=True,
            trade_id=trade_id,
            symbol=signal.symbol,
            action=signal.action,
            amount=amount,
            duration=duration,
            profit=0.0,
        )

    def close(self) -> None:
        self._connected = False
