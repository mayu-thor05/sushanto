import logging
import os
from datetime import datetime

def setup_logger(log_dir="backend/logs"):
    """Setups a basic logger."""

    # Ensure that the folder exists
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

     # Get the current datetime
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    # Create a new log filename based on the timestamp
    log_filename = os.path.join(log_dir, f"app_{timestamp}.log")

    logger = logging.getLogger('app_logger')
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_filename)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger