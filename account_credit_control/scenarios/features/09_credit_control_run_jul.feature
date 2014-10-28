###############################################################################
#
#    OERPScenario, OpenERP Functional Tests
#    Copyright 2012-2014 Camptocamp SA
#    Author Nicolas Bessi
##############################################################################

# Features Generic tags (none for all)
##############################################################################

@account_credit_control @account_credit_control_run  @account_credit_control_run_jul

Feature: Ensure that email credit line generation first pass is correct

    @account_credit_control_mark
    Scenario: mark lines
      Given there is "draft" credit lines
      And I mark all draft email to state "to_be_sent"
      Then the draft line should be in state "to_be_sent"

  @account_credit_control_run_month
  Scenario: Create run
    Given I need a "credit.control.run" with oid: credit_control.run7
    And having:
      | name |      value |
      | date | 2013-07-31 |
    When I launch the credit run
    Then my credit run should be in state "done"
    And the generated credit lines should have the following values:
     | balance |   date due | account | policy        |       date | partner     | channel | level | move line | policy level          | state | amount due | currency |
     |    1500 | 2013-04-30 | Debtors | 2 time policy | 2013-07-31 | customer_2  | letter  |     2 | SI_6      | 60 days last reminder | draft |       1500 | USD      |
     |    1500 | 2013-04-14 | Debtors | 2 time policy | 2013-07-31 | customer_3  | letter  |     2 | SI_9      | 60 days last reminder | draft |       1500 | USD      |
     | 1050.01 | 2013-04-30 | Debtors | 3 time policy | 2013-07-31 | customer_4  | letter  |     3 | SI_12     | 10 days last reminder | draft |    1050.01 | USD      |
     |    1050 | 2013-04-30 | Debtors | 3 time policy | 2013-07-31 | Donald Duck | letter  |     3 | SI_18     | 10 days last reminder | draft |       1050 |          |
     |    1050 | 2013-04-30 | Debtors | 3 time policy | 2013-07-31 | Gus Goose   | letter  |     3 | SI_19     | 10 days last reminder | draft |       1050 |          |
