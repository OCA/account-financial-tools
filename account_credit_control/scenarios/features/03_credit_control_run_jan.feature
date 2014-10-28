###############################################################################
#
#    OERPScenario, OpenERP Functional Tests
#    Copyright 2012-2014 Camptocamp SA
#    Author Nicolas Bessi
##############################################################################

# Features Generic tags (none for all)
##############################################################################

@account_credit_control  @account_credit_control_run  @account_credit_control_run_jan

Feature: Ensure that mail credit line generation first pass is correct

  Scenario: clean data
    Given I clean all the credit lines
    #Given I unreconcile and clean all move line

  @account_credit_control_run_month
  Scenario: Create run
    Given I need a "credit.control.run" with oid: credit_control.run1
    And having:
      | name |      value |
      | date | 2013-01-31 |
    When I launch the credit run
    Then my credit run should be in state "done"
    And the generated credit lines should have the following values:
     | balance |   date due | account | policy        |       date | partner    | channel | level | move line | policy level | state | amount due | currency |
     |     300 | 2013-01-18 | Debtors | 3 time policy | 2013-01-31 | customer_4 | email   |     1 | SI_10     | 10 days net  | draft |        300 |          |
