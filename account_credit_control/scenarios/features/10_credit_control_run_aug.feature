###############################################################################
#
#    OERPScenario, OpenERP Functional Tests
#    Copyright 2012-2014 Camptocamp SA
#    Author Nicolas Bessi
##############################################################################

# Features Generic tags (none for all)
##############################################################################

@account_credit_control @account_credit_control_run  @account_credit_control_run_aug

Feature: Ensure that ignore feature works as expected

  @account_credit_control_mark_as_ignore
  Scenario: mark last line as ignore
    Given I ignore the "Gus Goose" credit line at level "3" for move line "SI_19" with amount "1050.0"

  @account_credit_control_run_month_aug
  Scenario: Create run
    Given I need a "credit.control.run" with oid: credit_control.runignored
    And having:
      | name |      value |
      | date | 2013-08-30 |
    When I launch the credit run
    Then my credit run should be in state "done"

  @check_ignored_line
  Scenario: Check ignored lines
    Given I have for "Gus Goose" "2" credit lines at level "3" for move line "SI_19" with amount "1050.0" respectively in state "draft" and "ignored"
