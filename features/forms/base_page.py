import os
import time
from datetime import datetime as dt
from typing import Literal

import PyPDF2
import pandas as pd
from docx import Document
from openpyxl.utils.exceptions import InvalidFileException
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, Page, Locator, expect, Position

from features.utils.config_manager import ConfigManager
from features.utils.log_manager import LogManager


class BasePage:

    def __init__(self, page: Page):
        self.page = page
        self.config = ConfigManager()
        self.log = LogManager().get_logger()
        self.str_last_exported_file = None
        self.timeout = int(self.config.get("DYNAMIC_WAIT"))  # in milliseconds

    def _get_locator(self, pstr_selector: str | Locator):
        try:
            if isinstance(pstr_selector, str):
                return self.page.locator(pstr_selector)
            if isinstance(pstr_selector, Locator):
                return pstr_selector
        except ValueError as e:
            self.log.error(f"Invalid selector: {pstr_selector}. Error: {e}")
            raise ValueError(f"Invalid selector: {pstr_selector}") from e
        except Exception as e:
            self.log.error(f"Error getting locator for {pstr_selector}: {e}")
            raise Exception(f"Error getting locator for {pstr_selector}") from e

    def load_page_with_retry(self, pstr_url: str, pstr_locator: str):
        int_retries = int(self.config.get("RETRY_ATTEMPTS"))
        for attempt in range(int_retries):
            try:
                self.log.info(f"Navigating to {pstr_url} (attempt {attempt + 1}/{int_retries})")
                self.page.goto(url=pstr_url, timeout=self.timeout)
                self.page.wait_for_load_state("domcontentloaded", timeout=self.timeout)
                if not self.wait_for_element(pstr_locator, pint_timeout=self.timeout):
                    raise PlaywrightTimeoutError(f"Locator {pstr_locator} not found after navigation")
                self.log.info(f"Successfully loaded {pstr_url}")
                return True
            except PlaywrightTimeoutError as e:
                self.log.error(f"Timeout after attempt {attempt + 1} or error after navigation: {e}")
            except Exception as e:
                self.log.error(f"Error loading {pstr_url} on attempt {attempt + 1}: {e}")
            self.static_wait_with_polling()
        self.log.error(f"Failed to load {pstr_url} after {int_retries} attempts")
        return False

    def get_title(self):
        try:
            str_title = self.page.title()
            self.log.info(f"Title: {str_title}")
            return str_title
        except Exception as e:
            self.log.error(f"Error fetching title: {e}")
            raise Exception(f"Error fetching title: {e}") from e

    def get_element(self, pstr_selector: str | Locator):
        try:
            locator = self._get_locator(pstr_selector)
            if self.wait_for_element(locator):
                return locator
            return None
        except PlaywrightTimeoutError as e:
            self.log.error(f"Timeout: Element not found {pstr_selector}")
            raise PlaywrightTimeoutError(f"Element not found: {pstr_selector}") from e
        except ValueError as e:
            self.log.error(f"Invalid selector: {pstr_selector}. Error: {e}")
            raise ValueError(f"Invalid selector: {pstr_selector}") from e
        except Exception as e:
            self.log.error(f"Error getting element: {e}")
            raise Exception(f"Error getting element: {e}") from e

    def get_element_text(self, pstr_selector: str | Locator):
        try:
            locator = self._get_locator(pstr_selector)
            if self.wait_for_element(locator):
                text = locator.inner_text(timeout=self.timeout)
                self.log.info(f"Text of element '{pstr_selector}': {text}")
                return text
            return ""
        except Exception as e:
            self.log.error(f"Error getting element text: {e}")
            raise Exception(f"Error getting element text: {e}") from e

    def get_elements(self, pstr_selector: str | Locator):
        try:
            list_locators = self._get_locator(pstr_selector)
            if self.wait_for_element(list_locators):
                return list_locators.all()
            return None
        except Exception as e:
            self.log.error(f"Error getting elements: {e}")
            raise Exception(f"Error getting elements: {e}") from e

    def switch_tab(self, pstr_tab_name: str):
        try:
            locator = self.page.get_by_role(role="tab", name=pstr_tab_name, exact=True)
            self.click(locator)
            self.log.info(f"Switched to tab: {pstr_tab_name}")
        except PlaywrightTimeoutError as e:
            self.log.error(f"Timeout: Tab not found {pstr_tab_name}")
            raise PlaywrightTimeoutError(f"Tab not found: {pstr_tab_name}") from e
        except Exception as e:
            self.log.error(f"Error switching to tab {pstr_tab_name}: {e}")
            raise Exception(f"Error switching to tab {pstr_tab_name}: {e}") from e

    def click(self, pstr_selector: str | Locator, optional: bool = False):
        msg = f"Element not found: {pstr_selector}"
        try:
            locator = self._get_locator(pstr_selector)
            if self.wait_for_element(locator):
                locator.scroll_into_view_if_needed(timeout=self.timeout)
                locator.click(timeout=self.timeout)
                self.log.info(f"Clicked element: {pstr_selector}")
            else:
                if optional:
                    self.log.warning(msg + " (optional, skipping click)")
                else:
                    raise Exception(msg)
        except PlaywrightTimeoutError as e:
            if optional:
                self.log.warning(msg + " (optional, skipping click)")
            else:
                self.log.error(msg)
            raise PlaywrightTimeoutError(msg) from e
        except Exception as e:
            self.log.error(f"{msg}: {e}")
            raise Exception(f"{msg}: {e}") from e

    def type_text(self, pstr_selector: str | Locator, pstr_text: str, is_password: bool = False):
        try:
            obj_locator = self._get_locator(pstr_selector)
            if self.wait_for_element(obj_locator):
                obj_locator.fill(value="", timeout=self.timeout)  # Clears existing text
                obj_locator.fill(value=pstr_text, timeout=self.timeout)
                if is_password:
                    self.log.info(f"Typed text into {pstr_selector}: {'*' * len(pstr_text)}")
                else:
                    self.log.info(f"Typed text into {pstr_selector}: {pstr_text}")
            else:
                raise Exception(f"Input field not found: {pstr_selector}")
        except PlaywrightTimeoutError as e:
            self.log.error(f"Timeout: Unable to find input field {pstr_selector}")
            raise PlaywrightTimeoutError(f"Input field not found: {pstr_selector}") from e
        except Exception as e:
            self.log.error(f"Error typing in {pstr_selector}: {e}")
            raise Exception(f"Error typing in {pstr_selector}: {e}") from e

    def clear_text(self, pstr_selector: str | Locator):
        try:
            locator = self._get_locator(pstr_selector)
            if self.wait_for_element(pstr_selector):
                locator.fill(value="", timeout=self.timeout)
                self.log.info(f"Cleared text in {pstr_selector}")
            else:
                raise Exception(f"Input field not found: {pstr_selector}")
        except PlaywrightTimeoutError as e:
            self.log.error(f"Timeout: Unable to find input field {pstr_selector}")
            raise PlaywrightTimeoutError(f"Input field not found: {pstr_selector}") from e
        except Exception as e:
            self.log.error(f"Error clearing text in {pstr_selector}: {e}")
            raise Exception(f"Error clearing text in {pstr_selector}: {e}") from e

    def wait_for_visibility_of_text(self, pstr_selector: str | Locator, pstr_expected_text: str):
        try:
            locator = self._get_locator(pstr_selector)
            expect(locator.first).to_contain_text(pstr_expected_text, timeout=self.timeout)
            self.log.info(f"Text '{pstr_expected_text}' is visible on the page.")
            return True
        except (AssertionError, PlaywrightTimeoutError) as e:
            self.log.error(f"Timeout: Text '{pstr_expected_text}' not found within {self.timeout} ms.")
            raise AssertionError(f"Text '{pstr_expected_text}' not found") from e
        except Exception as e:
            self.log.error(f"Error waiting for text '{pstr_expected_text}': {e}")
            raise Exception(f"Error waiting for text '{pstr_expected_text}': {e}") from e

    def wait_for_element(self, pstr_selector: str | Locator, literal_state: Literal["attached", "detached", "hidden", "visible"] = "visible",
                         pint_timeout: int = None):
        int_timeout = pint_timeout if pint_timeout else self.timeout
        try:
            locator = self._get_locator(pstr_selector)
            if not literal_state:
                locator.first.wait_for(timeout=int_timeout)
            else:
                locator.first.wait_for(state=literal_state, timeout=int_timeout)
            self.static_wait_with_polling(pstr_selector, literal_state=literal_state)
            return True
        except PlaywrightTimeoutError as e:
            self.log.error(f"Timeout: Element '{pstr_selector}' not found within {int_timeout} ms: {e}")
            return False
        except Exception as e:
            self.log.error(f"Element '{pstr_selector}' not found: {e}")
            return False

    def static_wait_with_polling(self, pstr_selector: Locator | str = None,
                                 literal_state: Literal["attached", "detached", "hidden", "visible"] = "visible"):
        if not pstr_selector:
            int_static_wait_time = int(self.config.get("STATIC_WAIT"))
            time.sleep(int_static_wait_time)
            return True
        locator = self._get_locator(pstr_selector)
        end_time = time.time() + self.timeout / 1000
        while time.time() < end_time:
            try:
                if literal_state == "visible" and locator.first.is_visible(timeout=self.timeout):
                    self.log.info(f"Element {pstr_selector} is visible after waiting.")
                    return True
                elif literal_state == "attached" and locator.count() >= 1:
                    self.log.info(f"Element {pstr_selector} is attached after waiting.")
                    return True
                elif literal_state == "detached" and locator.count() == 0:
                    self.log.info(f"Element {pstr_selector} is detached after waiting.")
                    return True
                elif literal_state == "hidden" and locator.first.is_hidden():
                    self.log.info(f"Element {pstr_selector} is hidden after waiting.")
                    return True
            except PlaywrightTimeoutError as e:
                self.log.error(f"Error while waiting for element {pstr_selector}: {e}")
            time.sleep(1)
        return False

    def hover(self, pstr_selector: str | Locator, position: dict[str, int] | None = None):
        try:
            locator = self._get_locator(pstr_selector)
            if self.wait_for_element(locator):
                if position:
                    locator.hover(position=Position(**position), timeout=self.timeout)
                    self.log.info(f"Hovered over element at position {position}: {pstr_selector}")
                else:
                    locator.hover(timeout=self.timeout)
                    self.log.info(f"Hovered over element: {pstr_selector}")
            else:
                raise Exception(f"Element not found: {pstr_selector}")
        except PlaywrightTimeoutError as e:
            self.log.error(f"Timeout: Element not found {pstr_selector}")
            raise PlaywrightTimeoutError(f"Element not found: {pstr_selector}") from e
        except Exception as e:
            self.log.error(f"Error hovering over {pstr_selector}: {e}")
            raise Exception(f"Error hovering over {pstr_selector}: {e}") from e

    def get_element_by_text(self, pstr_text: str):
        try:
            self.log.info(f"Locating element using text: {pstr_text}")
            locator = self.page.get_by_text(text=pstr_text)
            if self.wait_for_element(locator):
                return locator
            return None
        except Exception as e:
            self.log.error(f"Error getting element by text: {e}")
            raise Exception(f"Error getting element by text: {e}") from e

    def get_element_count(self, pstr_locator: str | Locator):
        try:
            self.log.info(f"Getting element count for locator: {pstr_locator}")
            return self._get_locator(pstr_locator).count()
        except Exception as e:
            self.log.error(f"Error getting element count: {e}")
            raise Exception(f"Error getting element count: {e}") from e

    def is_element_disabled(self, pstr_selector: str | Locator):
        try:
            locator = self._get_locator(pstr_selector)
            if locator.get_attribute(name='disabled', timeout=self.timeout) is not None:
                self.log.info(f"Element '{pstr_selector}' is disabled.")
                return True
            self.log.info(f"Element '{pstr_selector}' is enabled.")
            return False
        except Exception as e:
            self.log.error(f"Error checking if element is disabled: {e}")
            raise Exception(f"Error checking if element is disabled: {e}") from e

    def is_element_visible(self, pstr_selector: str | Locator):
        try:
            locator = self._get_locator(pstr_selector)
            if locator is None:
                self.log.error(f"Locator for '{pstr_selector}' is None.")
                return False
            self.static_wait_with_polling(locator)
            if locator.is_visible(timeout=self.timeout):
                self.log.info(f"Element '{pstr_selector}' is visible.")
                return True
            self.log.error(f"Timeout: Element '{pstr_selector}' not visible within {self.timeout} ms.")
            return False
        except Exception as e:
            self.log.error(f"Error checking if element is visible: {e}")
            raise Exception(f"Error checking if element is visible: {e}") from e

    def switch_to_new_window_and_assert_url(self, pstr_expected_url: str):
        try:
            popup_page = self.page.wait_for_event("popup", timeout=self.timeout)
            if popup_page is None:
                raise Exception("No new browser window (popup) was captured.")
            popup_page.bring_to_front()
            popup_page.wait_for_function("document.location.href !== 'about:blank'", timeout=self.timeout)
            popup_page.wait_for_function(f"document.location.href.startsWith('{pstr_expected_url}')", timeout=self.timeout)
            popup_page.wait_for_load_state("load", timeout=self.timeout)
            actual_url = popup_page.url
            if not actual_url.startswith(pstr_expected_url):
                raise Exception(f"Expected URL starting with '{pstr_expected_url}', but got '{actual_url}'")
            self.log.info(f"Switched to new window and validated the URL: {actual_url}")
            popup_page.close()
            self.page.bring_to_front()
            return True
        except PlaywrightTimeoutError:
            error_msg = f"Timeout: New browser window did not open or load for expected URL: '{pstr_expected_url}'"
            self.log.error(error_msg)
            raise PlaywrightTimeoutError(error_msg)
        except Exception as e:
            error_msg = f"Error verifying new browser window URL: {e}"
            self.log.error(error_msg)
            raise Exception(error_msg) from e

    def drag_and_drop_element(self, source: str | Locator, target: str | Locator):
        source_selector = self._get_locator(source)
        target_selector = self._get_locator(target)
        if not (self.wait_for_element(source_selector) and self.wait_for_element(target_selector)):
            return False
        box_source = source_selector.bounding_box()
        box_target = target_selector.bounding_box()
        if not box_source or not box_target:
            raise Exception("Could not retrieve bounding boxes for drag and drop.")
        # move to center of source, press, move to center of target, release
        self.page.mouse.move(box_source["x"] + box_source["width"] / 2,
                             box_source["y"] + box_source["height"] / 2)
        self.page.mouse.down()
        self.page.mouse.move(box_target["x"] + box_target["width"] / 2,
                             box_target["y"] + box_target["height"] / 2,
                             steps=15)
        self.page.mouse.up()
        self.log.info(f"Dragged element from '{source}' to '{target}'")
        return True

    def select_dropdown_value(self, pstr_select: str, pstr_option: str):
        try:
            self.page.select_option(selector=pstr_select, value=pstr_option)
            self.log.info(f"Selected option '{pstr_option}' from dropdown '{pstr_select}'")
            return True
        except PlaywrightTimeoutError as e:
            self.log.error(f"Timeout: Unable to select option '{pstr_option}' from dropdown '{pstr_select}': {e}")
            return False
        except Exception as e:
            self.log.error(f"Error selecting option '{pstr_option}' from dropdown '{pstr_select}': {e}")
            return False

    def handle_dialog(self):
        try:
            self.page.on("dialog", lambda dialog: dialog.accept())
            self.log.info("Dialog accepted.")
        except Exception as e:
            self.log.error(f"Error handling dialog: {e}")
            raise Exception(f"Error handling dialog: {e}") from e

    def download_file(self, pstr_locator: str, file_type: str = "xlsx"):
        try:
            str_export_folder = self.config.exports_path
            str_filename = dt.now().strftime('%Y_%m_%d_%H_%M_%S')
            self.str_last_exported_file = os.path.join(str_export_folder, f"{str_filename}.{file_type}")
            with self.page.expect_download(timeout=self.timeout) as download_info:
                self.click(pstr_locator)
                self.static_wait_with_polling()
            download = download_info.value
            download.save_as(self.str_last_exported_file)
            self.log.info(f"Exported file at: {self.str_last_exported_file}")
            self.static_wait_with_polling()
            return bool(download)
        except Exception as e:
            self.log.error(f"Error downloading file: {e}")
            raise Exception(f"Error downloading file: {e}") from e

    def check_data_in_excel(self, expected_text: str):
        try:
            df = pd.read_excel(self.str_last_exported_file, header=None)
            return df.astype(str).map(lambda x: expected_text in x).any().any()
        except FileNotFoundError as e:
            self.log.error(f"File not found: {self.str_last_exported_file}")
            raise FileNotFoundError(f"File not found: {self.str_last_exported_file}") from e
        except InvalidFileException as e:
            self.log.error(f"Invalid Excel file: {self.str_last_exported_file} - {e}")
            raise InvalidFileException(f"Invalid Excel file: {self.str_last_exported_file} - {e}")
        except Exception as e:
            self.log.error(f"Error checking data in Excel: {e}")
            raise Exception(f"Error checking data in Excel: {e}") from e

    def check_data_in_pdf(self, expected_text: str):
        try:
            with open(self.str_last_exported_file, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text = page.extract_text()
                    if text and expected_text in text:
                        return True
            return False
        except FileNotFoundError as e:
            self.log.error(f"File not found: {self.str_last_exported_file}")
            raise FileNotFoundError(f"File not found: {self.str_last_exported_file}") from e
        except Exception as e:
            self.log.error(f"Error checking data in PDF: {e}")
            raise Exception(f"Error checking data in PDF: {e}") from e

    def check_data_in_word(self, expected_text: str):
        try:
            doc = Document(self.str_last_exported_file)
            for para in doc.paragraphs:
                if expected_text in para.text:
                    return True
            return False
        except FileNotFoundError as e:
            self.log.error(f"File not found: {self.str_last_exported_file}")
            raise FileNotFoundError(f"File not found: {self.str_last_exported_file}") from e
        except Exception as e:
            self.log.error(f"Error checking data in Word document: {e}")
            raise Exception(f"Error checking data in Word document: {e}") from e

    def click_and_capture_popup(self, pstr_selector: str):
        try:
            with self.page.expect_popup() as popup_info:
                self.page.click(pstr_selector)
            popup_page = popup_info.value
            popup_page.bring_to_front()
            self.log.info(f"Captured popup for selector: {pstr_selector}")
            return popup_page
        except Exception as e:
            self.log.error(f"Error capturing popup for selector '{pstr_selector}': {e}")
            raise Exception(f"Error capturing popup for selector '{pstr_selector}': {e}") from e

    def switch_to_new_window_and_assert_title(self, pstr_selector: str | Locator, pstr_expected_title: str):
        try:
            popup_page = getattr(self, "popup_page", None)
            if popup_page is None:
                raise Exception("Popup page not found. Did you forget to call click_more_link first?")
            popup_page.bring_to_front()
            popup_page.wait_for_load_state("load", timeout=self.timeout)
            str_selector = pstr_selector
            if not self.is_element_visible(str_selector):
                raise Exception(f"Expected header element not visible for selector: {str_selector}")
            str_actual_page_title = popup_page.locator(str_selector).text_content().strip()
            if pstr_expected_title not in str_actual_page_title.upper():
                raise Exception(f"Expected '{pstr_expected_title}' in header, but got '{str_actual_page_title}'")
            self.log.info(f"Validated new tab title: '{str_actual_page_title}' contains '{pstr_expected_title}'")
            popup_page.close()
            self.page.bring_to_front()
            return True
        except PlaywrightTimeoutError:
            error_msg = f"Timeout: New browser window did not load or show expected title: '{pstr_expected_title}'"
            self.log.error(error_msg)
            raise PlaywrightTimeoutError(error_msg)
        except Exception as e:
            error_msg = f"Error verifying new browser window title: {e}"
            self.log.error(error_msg)
            raise Exception(error_msg) from e

    def open_new_page(self, pstr_page_open_selector: str | Locator):
        with self.page.context.expect_page() as new_page_info:
            self.click(pstr_page_open_selector)
        return new_page_info.value

    def date_diff_in_days(self, pstr_date_1: str, pstr_date_2: str):
        str_date_format = "%b-%d-%Y"
        try:
            date_1 = dt.strptime(pstr_date_1, str_date_format)
            date_2 = dt.strptime(pstr_date_2, str_date_format)
            return abs((date_1 - date_2).days)
        except ValueError as e:
            self.log.error(f"Error parsing dates '{pstr_date_1}' or '{pstr_date_2}': {e}")
            raise ValueError(f"Error parsing dates '{pstr_date_1}' or '{pstr_date_2}': {e}") from e
