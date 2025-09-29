import base64
import os
import platform
import subprocess
import time
from functools import wraps
from pathlib import Path
from typing import Any

import allure
import pytest
from pytest_html import extras

from features.utils.config_manager import ConfigManager, is_ci
from features.utils.log_manager import LogManager


class ReportManager:
    def __init__(self):
        self.config = ConfigManager()
        self.log = LogManager().get_logger()
        self.network_calls = []
        self.EXTENSIONS = ('.js', '.css', '.woff', '.woff2', '.ttf', '.otf', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.map')
        self.KEYWORDS = ('google-analytics', 'sentry', 'hotjar', 'intercom', 'segment', 'datadog')

    def attach_video_to_report(self) -> None:
        if not is_ci():
            video_files = list(Path(self.config.video_path).glob("*.webm"))
            if video_files:
                video_file = video_files[0]
                with open(video_file, "rb") as f:
                    allure.attach(f.read(), name="playwright-video", attachment_type=allure.attachment_type.WEBM)
            else:
                self.log.warning("No video files found in the video directory.")
            if os.path.exists(self.config.trace_path):
                with open(self.config.trace_path, "rb") as f:
                    allure.attach(f.read(), name="playwright-trace")
        else:
            self.log.info("Skipping video & trace file attachment in CI environment.")

    def add_environment_info_to_report(self, session: pytest.Session) -> None:
        dynamic_wait_time = int(self.config.get('DYNAMIC_WAIT')) // 1000
        env_info = {
            'Browser': self.config.get('BROWSER'),
            'Static_Wait_Time': f"{self.config.get('STATIC_WAIT')} seconds",
            'Dynamic_Wait_Time': f"{dynamic_wait_time} seconds",
            'CI_Execution': is_ci(),
            'GitHub_Run_ID': os.getenv('GITHUB_RUN_ID', 'N/A'),
            'Run_Number': os.getenv('GITHUB_RUN_NUMBER', 'N/A'),
            'Workflow': os.getenv('GITHUB_WORKFLOW', 'N/A'),
            'Job': os.getenv('GITHUB_JOB', 'N/A'),
            'Ref': os.getenv('GITHUB_REF', 'N/A'),
            'user': os.getenv('GITHUB_ACTOR') or os.getenv('USERNAME') or os.getenv('USER'),
            'Platform': platform.system(),
            'Python_Version': platform.python_version(),
        }
        allure_result_dir = self.config.allure_results_path or session.config.option.allure_report_dir
        os.makedirs(allure_result_dir, exist_ok=True)
        str_env_file_path = os.path.join(allure_result_dir, 'environment.properties')
        with open(str_env_file_path, mode='w', encoding='utf-8') as f:
            for key, value in env_info.items():
                f.write(f'{key.upper()}={str(value).upper()}\n')

    @staticmethod
    def skip_scenarios_in_report(feature, scenario) -> None:
        if 'skipped' in feature.tags:
            pytest.skip(f"Skipping feature: {feature.name} due to 'skipped' tag")
        if 'skipped' in scenario.tags:
            pytest.skip(f"Skipping scenario: {scenario.name} due to 'skipped' tag")

    @staticmethod
    def add_labels_to_report(suite: str, feature: str, story: str, *tags: str) -> Any:
        def decorator(func):
            @allure.suite(suite)
            @allure.feature(feature)
            @allure.story(story)
            @allure.tag(*tags)
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def attach_screenshots_on_each_step(self, request, step) -> None:
        if 'ui' in request.node.keywords:
            page = request.getfixturevalue("page")
            if not page:
                return
            try:
                if not page.is_closed():
                    screenshot = page.screenshot()
                    allure.attach(screenshot, name=f"Step: {step.name}", attachment_type=allure.attachment_type.PNG)
                else:
                    self.log.error("Skipping screenshot: Page is already closed")
            except Exception as e:
                self.log.error(f"Screenshot failed: {e}")

    def intercept_network_calls(self, request) -> None:
        if 'ui' in request.node.keywords:
            page = request.getfixturevalue("page")
            if not page:
                return
            try:
                if not page.is_closed():
                    if not hasattr(page, "_network_listeners_attached"):
                        def log_request(requester):
                            if not requester.url.endswith(self.EXTENSIONS) and not (any(key in requester.url for key in self.KEYWORDS)):
                                self.network_calls.append({
                                    "type": "Request",
                                    "method": requester.method,
                                    "url": requester.url,
                                    "status": ""
                                })

                        def log_response(response):
                            if not response.url.endswith(self.EXTENSIONS) and not (any(key in response.url for key in self.KEYWORDS)):
                                self.network_calls.append({
                                    "type": "Response",
                                    "method": "",
                                    "url": response.url,
                                    "status": response.status
                                })

                        page.on("request", log_request)
                        page.on("response", log_response)
                        page._network_listeners_attached = True
                else:
                    self.log.error("[intercept_network_calls] Skipping network interception: Page is already closed")
            except Exception as e:
                self.log.error(f"[intercept_network_calls] Network interception failed: {e}")

    def write_network_calls_to_html(self) -> None:
        html_header = '<html><head><title>Network Calls</title></head><body><table border="1"><tr><th>Type</th><th>Method</th><th>URL</th><th>Status</th></tr>'
        html_footer = "</table></body></html>"
        rows = []
        for call in self.network_calls:
            row = f"<tr><td>{call['type']}</td><td>{call['method']}</td><td>{call['url']}</td><td>{call['status']}</td></tr>"
            rows.append(row)
        with open(self.config.network_calls_path, "w", encoding="utf-8") as f:
            f.write(html_header + "".join(rows) + html_footer)

    def attach_screenshot_on_failure(self, request, step) -> None:
        if is_ci() and 'ui' in request.node.keywords:
            try:
                page = request.getfixturevalue("page")
                if page and not page.is_closed():
                    screenshot = page.screenshot()
                    allure.attach(screenshot, name=f"Step failed: {step.name}", attachment_type=allure.attachment_type.PNG)
            except Exception as e:
                self.log.error(f"Screenshot failed: {e}")

    def attach_screenshot_to_report(self, outcome, call: pytest.CallInfo) -> None:
        try:
            report = outcome.get_result()
            if call.when == "call":
                screenshot = getattr(pytest, "extra_screenshot", None)
                if screenshot and os.path.exists(screenshot):
                    if not hasattr(report, "extra"):
                        report.extra = []
                    with open(screenshot, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode("utf-8")
                        html_img = f'<img src="data:image/png;base64,{encoded}" />'
                        report.extra.append(extras.html(html_img))
                pytest.extra_screenshot = None
        except Exception as e:
            self.log.error(f"Error attaching screenshot: {e}")

    def run_report(self) -> None:
        int_wait_time = int(self.config.get("STATIC_WAIT"))
        time.sleep(int_wait_time)
        os.chdir(self.config.root_dir)
        allure_cmd = "allure.bat" if platform.system() == "Windows" else "allure"
        try:
            if not is_ci():
                subprocess.run([allure_cmd, "generate", self.config.allure_results_path, "-o", self.config.allure_report_path, "--clean"],
                               check=True)
        except FileNotFoundError:
            self.log.error(f"Allure command '{allure_cmd}' not found. Skipping report generation.")
        except subprocess.CalledProcessError as e:
            self.log.error(f"Allure report generation failed for dir: {self.config.allure_results_path} with error: {e}")

