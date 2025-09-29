import allure
from pytest_bdd import scenario, given, when, then

from conftest import allure_labels

feature_path = "../feature_files/login.feature"


@given("user is on the login page")
@allure.step("user is on the login page")
def user_on_login_page():
    pass


@allure_labels("Login", "Validate Login with Valid Credentials", "Regression", "UI")
@scenario(feature_path, "validate login with valid credentials")
def test_login_valid_credentials():
    allure.dynamic.title("validate login with valid credentials")


@when("user enters valid username")
@allure.step("user enters valid username")
def enter_username():
    pass


@when("user enters valid password")
@allure.step("user enters valid password")
def enter_password():
    pass


@when("user clicks on submit button")
@allure.step("user clicks on submit button")
def click_submit():
    pass


@then("user should be navigated to the home page")
@allure.step("user should be navigated to the home page")
def validate_home_page():
    pass


@then("user should see the welcome message")
@allure.step("user should see the welcome message")
def validate_welcome_message():
    pass


@then("user should see the logout button")
@allure.step("user should see the logout button")
def validate_logout_button():
    pass


@allure_labels("Login", "Validate Login with Invalid Credentials", "Regression", "UI")
@scenario(feature_path, "validate login with invalid credentials")
def test_login_invalid_credentials():
    allure.dynamic.title("validate login with invalid credentials")


@when("user enters invalid username")
@allure.step("user enters invalid username")
def enter_invalid_username():
    pass


@when("user enters invalid password")
@allure.step("user enters invalid password")
def enter_invalid_password():
    pass


@then("user should see an error message")
@allure.step("user should see an error message")
def validate_error_message():
    pass
