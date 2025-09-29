import allure
import pytest
from pytest_bdd import scenario, given, when, then

from conftest import allure_labels
from features.forms.login.login_page import LoginPage
from features.utils.excel_manager import ExcelManager
from features.utils.secrets_manager import SecretsManager

feature_path = "../feature_files/login.feature"
secrets = SecretsManager()
excel = ExcelManager("creds.xlsx")
test_data = excel.read("Sheet1")


@pytest.fixture
def login_page(page) -> LoginPage:
    return LoginPage(page)


@given("user is on the login page")
@allure.step("user is on the login page")
def user_on_login_page(login_page: LoginPage):
    login_page.navigate()


@allure_labels("Login", "Validate Login with Valid Credentials", "Regression", "UI")
@pytest.mark.parametrize("username, password", [(data["VALID_USERNAME"], data["VALID_PASSWORD"]) for data in test_data])
@scenario(feature_path, "validate login with valid credentials")
def test_login_valid_credentials(username, password):
    allure.dynamic.title("validate login with valid credentials")


@when("user enters valid username")
@allure.step("user enters valid username")
def enter_username(login_page: LoginPage, username):
    login_page.enter_username(username)


@when("user enters valid password")
@allure.step("user enters valid password")
def enter_password(login_page: LoginPage, password):
    login_page.enter_password(password)


@when("user clicks on submit button")
@allure.step("user clicks on submit button")
def click_submit(login_page: LoginPage):
    login_page.click_login()


@then("user should see the welcome message")
@allure.step("user should see the welcome message")
def validate_welcome_message(login_page: LoginPage):
    login_page.validate_welcome_message()


@then("user should see the logout button")
@allure.step("user should see the logout button")
def validate_logout_button(login_page: LoginPage):
    login_page.validate_logout_button()


@allure_labels("Login", "Validate Login with Invalid Credentials", "Regression", "UI")
@pytest.mark.parametrize("username, password", [(data["INVALID_USERNAME"], data["INVALID_PASSWORD"]) for data in test_data])
@scenario(feature_path, "validate login with invalid credentials")
def test_login_invalid_credentials(username, password):
    allure.dynamic.title("validate login with invalid credentials")


@when("user enters invalid username")
@allure.step("user enters invalid username")
def enter_invalid_username(login_page: LoginPage, username):
    login_page.enter_username(username)


@when("user enters invalid password")
@allure.step("user enters invalid password")
def enter_invalid_password(login_page: LoginPage, password):
    login_page.enter_password(password)


@then("user should see an error message")
@allure.step("user should see an error message")
def validate_error_message(login_page: LoginPage):
    login_page.validate_error_message()
