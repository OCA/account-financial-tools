###############################################################################
#
#    OERPScenario, OpenERP Functional Tests
#    Copyright 2012-2014 Camptocamp SA
#    Author Nicolas Bessi
##############################################################################

# Features Generic tags (none for all)
##############################################################################

@account_credit_control  @account_credit_control_run  @account_credit_control_run_change_level

Feature: Ensure that manually changing an invoice level feature works as expected

  @account_credit_control_change_level
  Scenario: Change level
    Given I change level for invoice "SAJ/2014/0004" to "10 days net" of policy "3 time policy"
    Then wizard selected move lines should be:
      | name  |
      | SI_4  |
    When I confirm the level change
    And I should have "3" credit control lines overridden
    And one new credit control line of level "10 days net" related to invoice "SAJ/2014/0004"
    Then I force date of generated credit line to "2013-09-15"

  @account_credit_control_run_month_sept
  Scenario: Create run
    Given there is "draft" credit lines
    And I mark all draft email to state "to_be_sent"
    Then the draft line should be in state "to_be_sent"
    Given I need a "credit.control.run" with oid: credit_control.manual_change
    And having:
      | name |      value |
      | date | 2013-09-30 |
    When I launch the credit run
    Then my credit run should be in state "done"

  @account_credit_control_manual_next_step
  Scenario: Check manually managed line on run
    Given the invoice "SAJ/2014/0004" with manual changes
    And the invoice has "1" line of level "1" for policy "3 time policy"
    And the invoice has "1" line of level "2" for policy "3 time policy"
