"""
Central logging configuration.

Configures separate log levels for app modules vs dependencies,
keeping dependency noise down while maintaining verbose app logging.
"""

import logging
import sys
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"


def setup_logging(
    app_level: int = logging.DEBUG,
    dep_level: int = logging.INFO,
    log_to_console: bool = True,
    log_file_path: str | None = None,
) -> None:
    """
    Configure logging with separate levels for app vs dependencies.

    Args:
        app_level: Log level for app modules (default: DEBUG)
        dep_level: Log level for dependencies (default: INFO)
        log_to_console: Whether to log to stderr (default: True)
        log_file_path: Path to log file, or None to disable file logging
    """
    # Handlers set to lowest level - loggers control filtering
    handler_level = min(app_level, dep_level)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(handler_level)
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)

    # File handler
    if log_file_path:
        log_path = Path(log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(handler_level)
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)

    # Root logger controls dependency log level
    logging.getLogger().setLevel(dep_level)

    # App logger - more verbose (covers all ai_first_app.* modules)
    logging.getLogger("ai_first_app").setLevel(app_level)
