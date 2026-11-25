# signal-bot-quotex

A configurable trading signal bot for [Quotex](https://quotex.io). Parses text and JSON signals, enforces risk rules, and executes trades in either **mock** (simulated) or **real** (live Quotex) mode.

## Project structure

```
signal-bot-quotex/
├── run.py                 # convenience entry point
├── .env.example           # copy to .env and fill in your values
├── requirements.txt       # optional dependencies
├── README.md
├── LICENSE
├── signal_bot/            # application package
│   ├── __init__.py
│   ├── config.py          # settings from env (with validation)
│   ├── logger.py          # logging setup
│   ├── signals.py         # text/JSON signal parsing & validation
│   ├── risk.py            # risk manager + daily stats
│   └── trader.py          # mock + real Quotex trade execution
└── tests/
    └── test_signal_bot.py # unit tests (stdlib unittest)
```

## Quick start

```bash
# 1. Copy the example env file
cp .env.example .env
# 2. Edit .env (set SIGNAL_BOT_MODE=mock to start)
# 3. Run
python3 run.py --config-check
python3 run.py parse "BUY EURUSD 5m"
python3 run.py run --signal "BUY GBPUSD 5m"
```

### Interactive mode

```bash
python3 run.py run
> BUY EURUSD 5m
> status
> PUT USDJPY 1m
> quit
```

## Modes

| Mode | Behavior |
|------|----------|
| `mock` | Simulates trades (~55% win rate, 80% payout). No network, no risk. |
| `real` | Connects to Quotex via websocket and places live trades. Requires `QUOTEX_SSID` or `QUOTEX_EMAIL`/`QUOTEX_PASSWORD`. |

## Signal formats

**Text:** `BUY EURUSD 5m`, `CALL GBPUSD 5M`, `PUT USDJPY 1`

**JSON:** `{"action": "BUY", "symbol": "EURUSD", "duration": 5, "duration_unit": "m", "confidence": 0.9}`

Supported actions: `buy/call/up/bull` or `sell/put/down/bear`.
Duration units: `m` (minutes, default) or `s` (seconds).

## Risk management

The bot enforces per-day limits before every trade:

- `MAX_DAILY_LOSS` — stop trading once cumulative profit ≤ negative limit
- `MAX_DAILY_PROFIT` — stop once daily profit target is hit
- `MAX_CONCURRENT_TRADES` — max open trades at once
- `MIN_CONFIDENCE` — reject signals below this confidence (0–1)

## Development

```bash
# Install optional deps
pip install -r requirements.txt

# Run tests
python3 -m unittest discover -s tests -v
```

## License

MIT License — see [LICENSE](LICENSE).
