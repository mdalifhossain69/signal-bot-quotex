"""Risk management for the signal bot."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from .config import Config
from .signals import Signal


@dataclass
class TradeResult:
    """Outcome of a trade execution."""

    success: bool
    trade_id: str
    symbol: str
    action: str
    amount: float
    duration: int
    profit: float = 0.0
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class DailyStats:
    """Running statistics for the current trading day."""

    date: str = ""
    trades: int = 0
    wins: int = 0
    losses: int = 0
    total_profit: float = 0.0
    total_volume: float = 0.0

    def reset_for_date(self, date_str: str) -> None:
        if self.date != date_str:
            self.date = date_str
            self.trades = 0
            self.wins = 0
            self.losses = 0
            self.total_profit = 0.0
            self.total_volume = 0.0

    @property
    def win_rate(self) -> float:
        if self.trades == 0:
            return 0.0
        return self.wins / self.trades


class RiskManager:
    """Enforces risk rules before trades are placed."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.stats = DailyStats()
        self.open_trades: dict[str, TradeResult] = {}

    def _today(self) -> str:
        return time.strftime("%Y-%m-%d")

    def can_trade(self, signal: Signal, amount: float) -> tuple[bool, Optional[str]]:
        """Return (allowed, reason). If not allowed, reason explains why."""
        self.stats.reset_for_date(self._today())

        if amount <= 0:
            return False, "trade amount must be positive"

        if len(self.open_trades) >= self.config.max_concurrent_trades:
            return False, (
                f"max concurrent trades reached ({self.config.max_concurrent_trades})"
            )

        if self.stats.total_profit <= -abs(self.config.max_daily_loss):
            return False, f"daily loss limit reached ({self.config.max_daily_loss})"

        if self.stats.total_profit >= self.config.max_daily_profit:
            return False, f"daily profit target reached ({self.config.max_daily_profit})"

        if signal.confidence < self.config.min_confidence:
            return False, (
                f"signal confidence {signal.confidence} below minimum "
                f"{self.config.min_confidence}"
            )

        return True, None

    def record(self, result: TradeResult) -> None:
        """Record a completed trade result."""
        self.stats.reset_for_date(self._today())
        self.stats.trades += 1
        self.stats.total_profit += result.profit
        self.stats.total_volume += result.amount
        if result.profit > 0:
            self.stats.wins += 1
        elif result.profit < 0:
            self.stats.losses += 1
        self.open_trades.pop(result.trade_id, None)

    def open_trade(self, trade_id: str) -> None:
        self.open_trades[trade_id] = TradeResult(
            success=False,
            trade_id=trade_id,
            symbol="",
            action="",
            amount=0.0,
            duration=0,
        )

    def summary(self) -> dict:
        self.stats.reset_for_date(self._today())
        return {
            "date": self.stats.date,
            "trades": self.stats.trades,
            "wins": self.stats.wins,
            "losses": self.stats.losses,
            "win_rate": round(self.stats.win_rate, 4),
            "total_profit": round(self.stats.total_profit, 4),
            "total_volume": round(self.stats.total_volume, 4),
            "open_trades": len(self.open_trades),
        }
