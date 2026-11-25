"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


def _getenv(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(key, default)


def _getenv_bool(key: str, default: bool = False) -> bool:
    val = _getenv(key)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _getenv_int(key: str, default: int) -> int:
    val = _getenv(key)
    if val is None or val.strip() == "":
        return default
    try:
        return int(val.strip())
    except ValueError:
        return default


def _getenv_float(key: str, default: float) -> float:
    val = _getenv(key)
    if val is None or val.strip() == "":
        return default
    try:
        return float(val.strip())
    except ValueError:
        return default


@dataclass(frozen=True)
class Config:
    """Runtime configuration for the signal bot."""

    # Quotex credentials / endpoint
    quotex_email: Optional[str] = None
    quotex_password: Optional[str] = None
    quotex_ssid: Optional[str] = None
    quotex_demo: bool = True
    quotex_wss_url: str = "wss://wsb2.qxbroker.com/socket.io/?EIO=4&transport=websocket"

    # Bot behavior
    mode: str = "mock"  # mock | real
    default_symbol: str = "EURUSD"
    default_amount: float = 1.0
    default_duration: int = 5  # minutes
    default_duration_unit: str = "m"

    # Risk management
    max_daily_loss: float = 20.0
    max_daily_profit: float = 100.0
    max_concurrent_trades: int = 1
    min_confidence: float = 0.0

    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            quotex_email=_getenv("QUOTEX_EMAIL"),
            quotex_password=_getenv("QUOTEX_PASSWORD"),
            quotex_ssid=_getenv("QUOTEX_SSID"),
            quotex_demo=_getenv_bool("QUOTEX_DEMO", True),
            quotex_wss_url=_getenv("QUOTEX_WSS_URL", cls.quotex_wss_url),
            mode=_getenv("SIGNAL_BOT_MODE", "mock"),
            default_symbol=_getenv("DEFAULT_SYMBOL", "EURUSD"),
            default_amount=_getenv_float("DEFAULT_AMOUNT", 1.0),
            default_duration=_getenv_int("DEFAULT_DURATION", 5),
            default_duration_unit=_getenv("DEFAULT_DURATION_UNIT", "m"),
            max_daily_loss=_getenv_float("MAX_DAILY_LOSS", 20.0),
            max_daily_profit=_getenv_float("MAX_DAILY_PROFIT", 100.0),
            max_concurrent_trades=_getenv_int("MAX_CONCURRENT_TRADES", 1),
            min_confidence=_getenv_float("MIN_CONFIDENCE", 0.0),
            log_level=_getenv("LOG_LEVEL", "INFO"),
            log_file=_getenv("LOG_FILE"),
        )

    def validate(self) -> list[str]:
        """Return a list of validation error messages (empty if valid)."""
        errors: list[str] = []
        if self.mode not in {"mock", "real"}:
            errors.append(f"SIGNAL_BOT_MODE must be 'mock' or 'real', got {self.mode!r}")
        if self.default_amount <= 0:
            errors.append("DEFAULT_AMOUNT must be positive")
        if self.default_duration <= 0:
            errors.append("DEFAULT_DURATION must be positive")
        if self.max_concurrent_trades < 1:
            errors.append("MAX_CONCURRENT_TRADES must be >= 1")
        if not 0 <= self.min_confidence <= 1:
            errors.append("MIN_CONFIDENCE must be between 0 and 1")
        if self.mode == "real" and not (self.quotex_ssid or (self.quotex_email and self.quotex_password)):
            errors.append("QUOTEX_SSID or QUOTEX_EMAIL/QUOTEX_PASSWORD required in 'real' mode")
        return errors
