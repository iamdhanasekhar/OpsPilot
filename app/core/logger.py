
import logging
import sys

from app.core.config import settings


def setup_logging() -> None:
    """
    Configure centralized application logging.
    """

    log_level = getattr(
        logging,
        settings.LOG_LEVEL.upper(),
        logging.INFO,
    )

    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | %(levelname)-8s | "
            "%(name)s | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Prevent duplicate handlers during repeated initialization
    if not any(
        getattr(handler, "_opspilot_handler", False)
        for handler in root_logger.handlers
    ):
        console_handler._opspilot_handler = True
        root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named application logger.
    """
    return logging.getLogger(name)
