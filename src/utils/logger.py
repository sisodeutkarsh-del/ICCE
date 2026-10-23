"""
Structured logging module for the International Solar Technology Partner Matching Agent.
Provides console and rotating file logging with automatic sanitization of sensitive tokens.
"""

import logging
import re
import sys
from pathlib import Path
from typing import Optional


SENSITIVE_PATTERNS = [
    re.compile(r"(sk-or-v1-[a-zA-Z0-9]{16})[a-zA-Z0-9]+"),
    re.compile(r"(hf_[a-zA-Z0-9]{8})[a-zA-Z0-9]+"),
    re.compile(r"(AQ\.[a-zA-Z0-9_\-]{8})[a-zA-Z0-9_\-]+"),
    re.compile(r"(AIzaSy[a-zA-Z0-9_\-]{8})[a-zA-Z0-9_\-]+"),
]


class SanitizedFormatter(logging.Formatter):
    """Logging formatter that redacts detected API keys and secrets."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        sanitized = original
        for pattern in SENSITIVE_PATTERNS:
            sanitized = pattern.sub(r"\1...[REDACTED]", sanitized)
        return sanitized


def setup_logger(
    name: str = "solar_agent",
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """Configures and returns a logger instance with sanitization."""
    logger = logging.getLogger(name)
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # Avoid duplicate handlers if already configured
    if logger.handlers:
        return logger

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    fmt = "%(asctime)s | %(levelname)-7s | %(name)s:%(lineno)d - %(message)s"
    formatter = SanitizedFormatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (Optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


logger = setup_logger()
