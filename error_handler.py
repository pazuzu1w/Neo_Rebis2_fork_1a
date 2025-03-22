# error_handler.py
import traceback
from _logging import Logger


class ErrorHandler:
    def __init__(self):
        self.logger = Logger()

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle an exception"""
        self.logger.error(f"Uncaught exception: {exc_type.__name__}: {exc_value}")
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        self.logger.error(f"Traceback:\n{tb_str}")

    def install_global_handler(self):
        """Install a global exception handler"""
        import sys
        sys.excepthook = self.handle_exception