"""
Configuration management.

Loads environment variables from .env and validates required settings.
"""

import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Valid log level names
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""

    pass


@dataclass
class Config:
    """Application configuration."""

    openrouter_api_key: str
    openrouter_model: str
    log_level_app: int
    log_level_deps: int
    log_to_console: bool
    log_file_path: str | None


def _parse_log_level(value: str, default: int) -> int:
    """Parse a log level string to its int value."""
    value = value.strip().upper()
    if not value:
        return default
    if value not in LOG_LEVELS:
        return default
    return LOG_LEVELS[value]


def _parse_bool(value: str, default: bool) -> bool:
    """Parse a boolean string (case insensitive)."""
    value = value.strip().lower()
    if not value:
        return default
    return value in ("true", "1", "yes", "on")


def load_config() -> Config:
    """
    Load configuration from environment variables.

    Loads .env file if present, then validates required variables.

    Returns:
        Config object with validated settings

    Raises:
        ConfigError: If required variables are missing or empty
    """
    load_dotenv()

    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    model = os.getenv("OPENROUTER_MODEL", "").strip()
    log_level_app = _parse_log_level(os.getenv("LOG_LEVEL_APP", ""), logging.DEBUG)
    log_level_deps = _parse_log_level(os.getenv("LOG_LEVEL_DEPS", ""), logging.INFO)
    log_to_console = _parse_bool(os.getenv("LOG_TO_CONSOLE", ""), default=True)
    log_file_path = os.getenv("LOG_FILE_PATH", "").strip() or None

    errors = []

    if not api_key:
        errors.append(
            "OPENROUTER_API_KEY is required. Get one at https://openrouter.ai/keys"
        )

    if not model:
        errors.append(
            "OPENROUTER_MODEL is required (e.g., anthropic/claude-sonnet-4)"
        )

    if errors:
        raise ConfigError("\n".join(errors))

    return Config(
        openrouter_api_key=api_key,
        openrouter_model=model,
        log_level_app=log_level_app,
        log_level_deps=log_level_deps,
        log_to_console=log_to_console,
        log_file_path=log_file_path,
    )
