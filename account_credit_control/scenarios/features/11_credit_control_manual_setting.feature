###############################################################################
#
#    OERPScenario, OpenERP Functional Tests
#    Copyright 2012 Camptocamp SA
#    Author Nicolas Bessi
##############################################################################

# Features Generic tags (none for all)
##############################################################################

@account_credit_control  @account_credit_control_run  @account_credit_control_run_aug

Feature: Ensure that manually changing  an invoice level feature works as expected

  @account_credit_control_change_level
  Scenario: Change level
    Given I change level for invoice "SAJ/2014/0004" to "10 days net" of policy "3 time policy"
    Then wizard selected move lines should be:
      | name  |
      | SI_4  |
    When I confirm the level change
    And I should have "3" credit control lines overriden
    And one new credit control line of level "10 days net" related to invoice "SAJ/2014/0004"
