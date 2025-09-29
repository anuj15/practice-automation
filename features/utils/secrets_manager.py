import os

from dotenv import load_dotenv

from features.utils.config_manager import ConfigManager
from features.utils.log_manager import LogManager


class SecretsManager:

    def __init__(self):
        self.log = LogManager().get_logger()
        config = ConfigManager()
        env_file = os.path.join(config.root_dir, ".env")
        load_dotenv(env_file, override=True)

    def get_secret(self, key):
        value = os.getenv(key)
        if not value:
            self.log.error("Error: Invalid secret key: %s", key)
            raise KeyError(f"Invalid secret key: {key}")
        return value


if __name__ == "__main__":
    sm = SecretsManager()
    print(sm.get_secret("USERNAME"))
    print(sm.get_secret("PASSWORD"))
