"""studio_logger.py — Centralised logging for STUDIO.

Usage:
    from studio_logger import get_logger
    logger = get_logger(__name__)
    logger.info("Pipeline started")
    logger.error("API call failed: %s", error)

Log files are written to logs/studio.log with daily rotation (7 days kept).
Console output shows INFO and above. File output shows DEBUG and above.
"""
import logging
import logging.handlers
from pathlib import Path

_LOGS_DIR = Path(__file__).parent / "logs"
_LOGS_DIR.mkdir(exist_ok=True)

_formatter_file = logging.Formatter(
    "%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
_formatter_console = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")

_file_handler = logging.handlers.TimedRotatingFileHandler(
    _LOGS_DIR / "studio.log",
    when="midnight",
    backupCount=7,
    encoding="utf-8",
)
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(_formatter_file)

_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(_formatter_console)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger with file (DEBUG) and console (INFO) handlers.

    Args:
        name: Logger name — use __name__ from the calling module.

    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # Already configured
    logger.setLevel(logging.DEBUG)
    logger.addHandler(_file_handler)
    logger.addHandler(_console_handler)
    logger.propagate = False
    return logger
