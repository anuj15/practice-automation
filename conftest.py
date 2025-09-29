import os
import shutil
import time

import pytest
from playwright.sync_api import sync_playwright
from pytest_metadata.plugin import metadata_key

from features.utils.config_manager import ConfigManager, is_ci
from features.utils.log_manager import LogManager
from features.utils.report_manager import ReportManager

obj_config = ConfigManager()
logger = LogManager().get_logger()
report_manager = ReportManager()
bool_is_ci_env = is_ci()


@pytest.hookimpl
def pytest_configure(config: pytest.Config):
    config.option.htmlpath = obj_config.html_report_path
    if not bool_is_ci_env:
        config.option.allure_report_dir = obj_config.allure_results_path
    config.option.self_contained_html = True
    config.option.disable_warnings = True
    config.option.strict_markers = True
    config.option.reruns = 0
    config.option.color = "yes"
    config.option.timeout = 3000
    config.option.timeout_method = "thread"
    config.option.tb = "short"
    config.stash.setdefault(metadata_key, {})["Browser"] = obj_config.get("BROWSER")


@pytest.hookimpl
def pytest_html_report_title(report):
    report.title = obj_config.get("PROJECT")


@pytest.hookimpl
def pytest_sessionstart(session: pytest.Session):
    network_call_logs = obj_config.network_calls_path
    if os.path.exists(network_call_logs):
        with open(network_call_logs, "w", encoding="utf-8") as f:
            f.write("")
    str_report_dir = obj_config.report_path
    if not bool_is_ci_env:
        shutil.rmtree(str_report_dir, ignore_errors=True)
        os.makedirs(str_report_dir, exist_ok=True)
        os.makedirs(obj_config.allure_report_path, exist_ok=True)
        os.makedirs(obj_config.allure_results_path, exist_ok=True)
    log_file = obj_config.log_path
    if os.path.exists(log_file):
        with open(log_file, mode="w", encoding="utf-8") as f:
            f.write("")
    report_manager.add_environment_info_to_report(session)


@pytest.fixture(scope="session")
def browser():
    browser_name = obj_config.get("BROWSER")
    headless = obj_config.get("HEADLESS")
    with sync_playwright() as p:
        logger.info("Launching browser...")
        browser = getattr(p, browser_name).launch(headless=headless, args=["--start-maximized", "--disable-dev-shm-usage", "--no-sandbox",
                                                                           "--disable-gpu", "--disable-infobars", "--disable-extensions",
                                                                           "--enable-automation", "--ignore-certificate-errors"])
        yield browser
        browser.close()
        logger.info("Browser closed")


@pytest.hookimpl
def pytest_bdd_before_scenario(request, feature, scenario):
    report_manager.skip_scenarios_in_report(feature, scenario)


@pytest.fixture(scope="function")
def page(browser, request):
    headless = obj_config.get("HEADLESS")
    int_wait_time = int(obj_config.get("STATIC_WAIT"))
    width = int(obj_config.get("VIEWPORT_WIDTH"))
    height = int(obj_config.get("VIEWPORT_HEIGHT"))
    viewport = {"width": width, "height": height} if headless else None
    no_viewport = not headless
    record_video_size = {"width": width, "height": height} if not bool_is_ci_env else None
    record_video_dir = obj_config.video_path if not bool_is_ci_env else None
    context = browser.new_context(no_viewport=no_viewport, viewport=viewport, record_video_dir=record_video_dir, record_video_size=record_video_size)
    logger.info("New browser context created")
    page = context.new_page()
    logger.info("New page created in the browser context")
    if not bool_is_ci_env:
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        logger.info("Tracing started for the context")
    try:
        yield page
    finally:
        try:
            if not bool_is_ci_env:
                context.tracing.stop(path=obj_config.trace_path)
                logger.info("Tracing stopped for the context")
        except Exception as e:
            logger.error(f"Failed to stop tracing: {e}")
        try:
            context.close()
        except Exception as e:
            logger.error(f"Failed to close context: {e}")

        if not bool_is_ci_env:
            time.sleep(int_wait_time)
            report_manager.attach_video_to_report()


def allure_labels(suite, feature, story, *tags):
    return report_manager.add_labels_to_report(suite, feature, story, *tags)


@pytest.hookimpl
def pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args):
    report_manager.intercept_network_calls(request)
    if not bool_is_ci_env or step == scenario.steps[-1]:
        report_manager.attach_screenshots_on_each_step(request, step)


@pytest.hookimpl
def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    report_manager.attach_screenshot_on_failure(request, step)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call: pytest.CallInfo):
    outcome = yield
    report_manager.attach_screenshot_to_report(outcome, call)


@pytest.hookimpl
def pytest_sessionfinish(session: pytest.Session, exitstatus):
    report_manager.write_network_calls_to_html()
    report_manager.run_report()
