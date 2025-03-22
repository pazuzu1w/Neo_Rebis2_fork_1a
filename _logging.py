# logger.py
import logging
import os
from datetime import datetime


class Logger:
    def __init__(self, log_dir="logs", level=logging.INFO):
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self.logger = logging.getLogger("neo_rebis")
        self.logger.setLevel(level)

        # File handler
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(f"{log_dir}/neo_rebis_{timestamp}.log")
        file_handler.setLevel(level)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def debug(self, message):
        """Log a debug message"""
        self.logger.debug(message)

    def info(self, message):
        """Log an info message"""
        self.logger.info(message)

    def warning(self, message):
        """Log a warning message"""
        self.logger.warning(message)

    def error(self, message):
        """Log an error message"""
        self.logger.error(message)

    def critical(self, message):
        """Log a critical message"""
        self.logger.critical(message)