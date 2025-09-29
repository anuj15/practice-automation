@ui @regression
Feature: Login Functionality

  Background:
    Given user is on the login page

  Scenario: validate login with valid credentials
    When user enters valid username
    And user enters valid password
    And user clicks on submit button
    Then user should be navigated to the home page
    And user should see the welcome message
    And user should see the logout button

  Scenario: validate login with invalid credentials
    When user enters invalid username
    And user enters invalid password
    And user clicks on submit button
    Then user should see an error message
