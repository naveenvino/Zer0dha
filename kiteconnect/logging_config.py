import logging
import os

def setup_logging(log_file: str = "kiteconnect.log", level=logging.INFO):
    """
    Sets up a basic logging configuration.

    :param log_file: The name of the log file.
    :param level: The logging level (e.g., logging.INFO, logging.DEBUG).
    """
    log_directory = "logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    log_path = os.path.join(log_directory, log_file)

    # Create a logger
    logger = logging.getLogger("kiteconnect_logger")
    logger.setLevel(level)

    # Create a file handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(level)

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # Create a formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
