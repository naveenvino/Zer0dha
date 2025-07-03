import logging
from kiteconnect import setup_logging

# Setup logging
logger = setup_logging(log_file="my_app.log", level=logging.INFO)

logger.info("This is an informational message.")
logger.warning("This is a warning message.")
logger.error("This is an error message.")
logger.debug("This is a debug message. (Will not be shown if level is INFO)")

try:
    1 / 0
except ZeroDivisionError as e:
    logger.exception("An exception occurred:")
