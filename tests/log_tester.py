from app.core.logger import setup_logging, get_logger

setup_logging()

logger = get_logger("opspilot")

logger.debug("Debug message")
logger.info("Application started")
logger.warning("This is a warning")
logger.error("Something went wrong")

try:
    1 / 0
except ZeroDivisionError:
    logger.exception("Unexpected calculation failure")