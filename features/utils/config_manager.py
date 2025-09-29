import os
from pathlib import Path

import yaml


def is_ci():
    return os.getenv("GITHUB_ACTIONS", "false").lower() == "true"


class ConfigManager:
    def __init__(self):
        self.root_dir = os.getenv("GITHUB_WORKSPACE") or str(Path(__file__).resolve().parents[2])
        config_file = os.path.join(self.root_dir, "config.yml")
        with open(config_file, encoding="utf-8") as file:
            self.data = yaml.safe_load(file)

    def get(self, key):
        try:
            env_value = os.getenv(key)
            if env_value is not None:
                return env_value
            return self.data.get(key)
        except KeyError as e:
            raise KeyError(f"Key {key} not found in configuration.") from e

    @property
    def test_data_path(self):
        return os.path.join(self.root_dir, self.get("TEST_DATA_PATH"))

    @property
    def report_path(self):
        return os.path.join(self.root_dir, self.get("REPORT_PATH"))

    @property
    def exports_path(self):
        return os.path.join(self.root_dir, self.get("EXPORTS_PATH"))

    @property
    def log_path(self):
        return os.path.join(self.root_dir, self.get("LOG_PATH"))

    @property
    def screenshot_path(self):
        return os.path.join(self.root_dir, self.get("SCREENSHOT_PATH"))

    @property
    def video_path(self):
        return os.path.join(self.root_dir, self.get("VIDEO_PATH"))

    @property
    def allure_results_path(self):
        return os.path.join(self.root_dir, self.get("ALLURE_RESULTS_PATH"))

    @property
    def allure_report_path(self):
        return os.path.join(self.root_dir, self.get("ALLURE_REPORT_PATH"))

    @property
    def html_report_path(self):
        return os.path.join(self.root_dir, self.get("HTML_REPORT_PATH"))

    @property
    def trace_path(self):
        return os.path.join(self.root_dir, self.get("TRACE_PATH"))

    @property
    def network_calls_path(self):
        return os.path.join(self.root_dir, self.get("NETWORK_CALLS_PATH"))


if __name__ == "__main__":
    config = ConfigManager()
    print("Browser:", config.get("BROWSER"))
    print("Height:", config.get("VIEWPORT_HEIGHT"))
    print("Test Data Path:", config.test_data_path)
    print("Report Path:", config.report_path)
    print("Log Path:", config.log_path)
    print("Screenshot Path:", config.screenshot_path)
    print("Video Path:", config.video_path)
    print("Allure Results Path:", config.allure_results_path)
    print("Allure Report Path:", config.allure_report_path)
    print("HTML Report Path:", config.html_report_path)
    print("Trace Path:", config.trace_path)
    print("Network Calls Path:", config.network_calls_path)
