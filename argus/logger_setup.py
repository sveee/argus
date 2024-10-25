import logging


def setup_logging():
    # Define the log format
    log_format = '[%(asctime)s] %(levelname)s | %(name)s:%(lineno)d | %(message)s'

    # Define the date format
    date_format = '%Y-%m-%d %H:%M:%S'

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,  # Set minimum log level to DEBUG
        format=log_format,  # Set log format
        datefmt=date_format,  # Set date format
        handlers=[logging.StreamHandler()],  # Only log to the console
    )
