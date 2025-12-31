"""Entry point for the AI-First Todo assistant."""

import logging
import sys

from ai_first_app.config import ConfigError, load_config
from ai_first_app.logging_config import setup_logging
from ai_first_app.cli import main

logger = logging.getLogger("ai_first_app")

if __name__ == "__main__":
    try:
        config = load_config()
    except ConfigError as e:
        print(f"Configuration error:\n{e}", file=sys.stderr)
        sys.exit(1)

    setup_logging(
        app_level=config.log_level_app,
        dep_level=config.log_level_deps,
        log_to_console=config.log_to_console,
        log_file_path=config.log_file_path,
    )

    # Log startup context
    logger.info(f"Model: {config.openrouter_model}")
    logger.info(f"Log levels: app={logging.getLevelName(config.log_level_app)}, deps={logging.getLevelName(config.log_level_deps)}")
    logger.info(f"Log output: console={config.log_to_console}, file={config.log_file_path or 'disabled'}")

    main(config)
