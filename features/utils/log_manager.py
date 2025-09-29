import logging
import os

from features.utils.config_manager import ConfigManager


class LogManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        config = ConfigManager()
        log_file = config.log_path
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        console_handler = logging.StreamHandler()
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')

        log_format = logging.Formatter("%(asctime)s - %(message)s")
        console_handler.setFormatter(log_format)
        file_handler.setFormatter(log_format)

        if not self.logger.hasHandlers():
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)

    def get_logger(self) -> logging.Logger:
        return self.logger


if __name__ == "__main__":
    log_manager = LogManager()
    logger = log_manager.get_logger()
    logger.info("This is an info message.")
    logger.error("This is an error message.")
