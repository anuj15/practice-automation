from playwright.sync_api import Page

from features.forms.base_page import BasePage
from features.forms.login import locators


class LoginPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)

    def navigate(self):
        url = self.config.get("BASE_URL") + locators.ENDPOINT
        self.load_page_with_retry(url, locators.USERNAME)

    def enter_username(self, username):
        self.type_text(locators.USERNAME, username)

    def enter_password(self, password):
        self.type_text(locators.PASSWORD, password, is_password=True)

    def click_login(self):
        self.click(locators.LOGIN_BUTTON)

    def validate_welcome_message(self):
        return self.wait_for_element(locators.LOGIN_TEXT)

    def validate_logout_button(self):
        return self.wait_for_element(locators.LOGOUT_BUTTON)

    def validate_error_message(self):
        return self.wait_for_element(locators.ERROR)
