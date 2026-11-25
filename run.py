#!/usr/bin/env python3
"""Convenience entry point for the signal bot."""

from __future__ import annotations

import sys

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except ImportError:
    pass

from signal_bot.main import main

if __name__ == "__main__":
    sys.exit(main())
