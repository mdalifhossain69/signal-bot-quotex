"""Logging setup for the signal bot."""

from __future__ import annotations

import logging
import sys
from typing import Optional

from .config import Config


def setup_logging(config: Config) -> logging.Logger:
    """Configure and return the application logger."""
    logger = logging.getLogger("signal_bot")
    logger.setLevel(getattr(logging, config.log_level.upper(), logging.INFO))
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if config.log_file:
        handler: logging.Handler = logging.FileHandler(config.log_file)
    else:
        handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(fmt)
    logger.addHandler(handler)

    logger.propagate = False
    return logger
