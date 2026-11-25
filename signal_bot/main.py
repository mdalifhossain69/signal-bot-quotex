"""Command-line entry point for the signal bot."""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from .config import Config
from .logger import setup_logging
from .risk import RiskManager
from .signals import Signal, is_valid, parse
from .trader import Trader


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="signal-bot",
        description="Quotex trading signal bot",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")
    parser.add_argument(
        "--mode",
        choices=["mock", "real"],
        help="Execution mode (default: mock, or SIGNAL_BOT_MODE env)",
    )
    parser.add_argument(
        "--config-check",
        action="store_true",
        help="Validate configuration and exit",
    )
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Run the bot interactively")
    run_p.add_argument("signal", nargs="?", help="Signal to execute (text or JSON)")
    run_p.add_argument("--amount", type=float, help="Trade amount")
    run_p.add_argument("--duration", type=int, help="Duration in minutes")
    run_p.add_argument("--symbol", help="Trading symbol (overrides signal)")

    sub.add_parser("status", help="Show risk/status summary")
    parse_p = sub.add_parser("parse", help="Parse a signal and print it")
    parse_p.add_argument("signal", help="Signal to parse")

    return parser


def run_bot(
    config: Config,
    logger,
    signal_text: Optional[str] = None,
    amount: Optional[float] = None,
    duration: Optional[int] = None,
    symbol: Optional[str] = None,
) -> int:
    errors = config.validate()
    if errors:
        for err in errors:
            logger.error("config error: %s", err)
        return 2

    trader = Trader(config)
    if not trader.connect():
        logger.error("failed to connect to trading backend")
        return 1

    risk = RiskManager(config)

    try:
        if signal_text:
            return _execute(
                config,
                logger,
                trader,
                risk,
                signal_text,
                amount=amount,
                duration=duration,
                symbol=symbol,
            )

        # Interactive loop
        logger.info("Signal bot running in %s mode. Type signals or 'quit'.", config.mode)
        print("Signal bot ready. Examples: 'BUY EURUSD 5m', '{\"action\":\"BUY\",\"symbol\":\"GBPUSD\"}'")
        while True:
            try:
                line = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not line or line.lower() in {"quit", "exit", "q"}:
                break
            if line.lower() in {"status", "stats"}:
                print(risk.summary())
                continue
            try:
                _execute(config, logger, trader, risk, line)
            except Exception as exc:  # noqa: BLE001 - keep interactive loop alive
                logger.error("signal error: %s", exc)
    finally:
        trader.close()

    return 0


def _execute(
    config,
    logger,
    trader,
    risk,
    signal_text: str,
    amount: Optional[float] = None,
    duration: Optional[int] = None,
    symbol: Optional[str] = None,
) -> int:
    signal = parse(signal_text).normalized()
    validation = is_valid(signal)
    if validation:
        logger.error("invalid signal: %s", "; ".join(validation))
        return 1

    logger.info("signal parsed: %s", signal.to_dict())

    amount = amount if amount is not None else config.default_amount
    duration = duration if duration is not None else signal.duration
    symbol = symbol if symbol is not None else signal.symbol
    signal = Signal(
        action=signal.action,
        symbol=symbol,
        duration=duration,
        duration_unit=signal.duration_unit,
        confidence=signal.confidence,
        source=signal.source,
        raw=signal.raw,
    )

    allowed, reason = risk.can_trade(signal, amount)
    if not allowed:
        logger.warning("trade rejected: %s", reason)
        print(f"REJECTED: {reason}")
        return 0

    result = trader.place_trade(signal, amount=amount, duration=duration)
    risk.record(result)

    status = "OK" if result.success else "FAILED"
    print(
        f"[{status}] {result.trade_id} {result.action.upper()} {result.symbol} "
        f"amount={result.amount} dur={result.duration}m profit={result.profit}"
    )
    if result.error:
        logger.error("trade error: %s", result.error)
    else:
        logger.info("trade result: %s", result.to_dict() if hasattr(result, "to_dict") else result)

    return 0 if result.success else 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    config = Config.from_env()
    if args.mode:
        config = Config(**{**config.__dict__, "mode": args.mode})

    logger = setup_logging(config)

    if args.config_check:
        errors = config.validate()
        if errors:
            for err in errors:
                print(f"CONFIG ERROR: {err}")
            return 2
        print("Configuration OK")
        print(config.__dict__)
        return 0

    if args.command == "status":
        risk = RiskManager(config)
        print(risk.summary())
        return 0

    if args.command in {"parse", None} and hasattr(args, "signal") and args.signal:
        try:
            signal = parse(args.signal).normalized()
            print(signal.to_dict())
            errs = is_valid(signal)
            if errs:
                print("validation warnings:", errs)
                return 1
        except Exception as exc:  # noqa: BLE001
            print(f"parse error: {exc}")
            return 1
        return 0

    if args.command == "run":
        return run_bot(
            config,
            logger,
            getattr(args, "signal", None),
            amount=getattr(args, "amount", None),
            duration=getattr(args, "duration", None),
            symbol=getattr(args, "symbol", None),
        )

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
