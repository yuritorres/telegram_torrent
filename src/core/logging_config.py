import logging
import os


def setup_logging(level: str = None) -> None:
    log_level = getattr(logging, (level or os.getenv('LOG_LEVEL', 'INFO')).upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
