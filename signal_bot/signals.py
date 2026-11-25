"""Signal parsing and validation.

Supports text signals such as::

    BUY EURUSD 1m 5min
    CALL GBPUSD 5M
    PUT USDJPY 1

and JSON signals such as::

    {"action": "BUY", "symbol": "EURUSD", "duration": 5, "duration_unit": "m"}
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional


# Direction aliases
DIRECTION_ALIASES = {
    "buy": "buy",
    "call": "buy",
    "up": "buy",
    "bull": "buy",
    "sell": "sell",
    "put": "sell",
    "down": "sell",
    "bear": "sell",
}

# Duration unit aliases
UNIT_ALIASES = {
    "m": "m",
    "min": "m",
    "mins": "m",
    "minute": "m",
    "minutes": "m",
    "s": "s",
    "sec": "s",
    "secs": "s",
    "second": "s",
    "seconds": "s",
}

TEXT_SIGNAL_RE = re.compile(
    r"""(?P<action>buy|call|up|bull|sell|put|down|bear)\s+
        (?P<symbol>[A-Za-z]{3,6})\s*
        (?:
            (?P<duration>\d+)\s*
            (?P<unit>m|min|mins|minute|minutes|s|sec|secs|second|seconds)?
        )?
    """,
    re.IGNORECASE | re.VERBOSE,
)


@dataclass(frozen=True)
class Signal:
    """A parsed trading signal."""

    action: str  # "buy" or "sell"
    symbol: str
    duration: int
    duration_unit: str = "m"
    confidence: float = 1.0
    source: str = "manual"
    raw: str = ""

    def normalized(self) -> "Signal":
        """Return a copy with normalized fields."""
        return Signal(
            action=self.action.lower(),
            symbol=self.symbol.upper(),
            duration=max(1, int(self.duration)),
            duration_unit=self.duration_unit.lower(),
            confidence=max(0.0, min(1.0, float(self.confidence))),
            source=self.source,
            raw=self.raw,
        )

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "symbol": self.symbol,
            "duration": self.duration,
            "duration_unit": self.duration_unit,
            "confidence": self.confidence,
            "source": self.source,
            "raw": self.raw,
        }


class SignalError(ValueError):
    """Raised when a signal cannot be parsed or is invalid."""


def parse_text(text: str, source: str = "text") -> Signal:
    """Parse a free-form text signal into a :class:`Signal`."""
    if not text or not text.strip():
        raise SignalError("empty signal text")

    text = text.strip()
    match = TEXT_SIGNAL_RE.search(text)
    if not match:
        raise SignalError(f"could not parse signal: {text!r}")

    action_raw = match.group("action").lower()
    action = DIRECTION_ALIASES.get(action_raw)
    if action is None:
        raise SignalError(f"unknown action in signal: {text!r}")

    symbol = match.group("symbol").upper()

    duration_str = match.group("duration")
    duration = int(duration_str) if duration_str else 5

    unit_raw = match.group("unit")
    unit = UNIT_ALIASES.get(unit_raw.lower(), "m") if unit_raw else "m"

    return Signal(
        action=action,
        symbol=symbol,
        duration=duration,
        duration_unit=unit,
        source=source,
        raw=text,
    ).normalized()


def parse_json(payload: str | dict, source: str = "json") -> Signal:
    """Parse a JSON signal (as a string or dict) into a :class:`Signal`."""
    if isinstance(payload, str):
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise SignalError(f"invalid JSON signal: {exc}") from exc
    else:
        data = payload

    if not isinstance(data, dict):
        raise SignalError("JSON signal must be an object")

    action_raw = str(data.get("action", "")).lower()
    action = DIRECTION_ALIASES.get(action_raw)
    if action is None:
        raise SignalError(f"missing or unknown action in JSON signal: {data!r}")

    symbol = str(data.get("symbol", "")).upper()
    if not symbol:
        raise SignalError("missing symbol in JSON signal")

    try:
        duration = int(data.get("duration", 5))
    except (TypeError, ValueError):
        duration = 5

    unit = str(data.get("duration_unit", data.get("unit", "m"))).lower()
    unit = UNIT_ALIASES.get(unit, "m")

    try:
        confidence = float(data.get("confidence", 1.0))
    except (TypeError, ValueError):
        confidence = 1.0

    return Signal(
        action=action,
        symbol=symbol,
        duration=duration,
        duration_unit=unit,
        confidence=confidence,
        source=source,
        raw=json.dumps(data) if isinstance(payload, str) else str(data),
    ).normalized()


def parse(signal: str | dict, source: Optional[str] = None) -> Signal:
    """Auto-detect and parse a text or JSON signal."""
    if isinstance(signal, dict):
        return parse_json(signal, source=source or "dict")

    text = str(signal).strip()
    # Heuristic: treat as JSON if it starts with '{' or '['
    if text.startswith("{") or text.startswith("["):
        return parse_json(text, source=source or "json")
    return parse_text(text, source=source or "text")


def is_valid(signal: Signal) -> list[str]:
    """Return validation error messages for a signal (empty if valid)."""
    errors: list[str] = []
    if signal.action not in {"buy", "sell"}:
        errors.append(f"invalid action: {signal.action!r}")
    if not re.fullmatch(r"[A-Za-z]{3,6}", signal.symbol):
        errors.append(f"invalid symbol: {signal.symbol!r}")
    if signal.duration < 1:
        errors.append(f"duration must be >= 1, got {signal.duration}")
    if not 0 <= signal.confidence <= 1:
        errors.append(f"confidence must be between 0 and 1, got {signal.confidence}")
    return errors
