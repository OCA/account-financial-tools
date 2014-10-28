###############################################################################
#
#    OERPScenario, OpenERP Functional Tests
#    Copyright 2012-2014 Camptocamp SA
#    Author Nicolas Bessi
##############################################################################

# Features Generic tags (none for all)
##############################################################################

@account_credit_control @account_credit_control_run  @account_credit_control_run_jun

Feature: Ensure that email credit line generation first pass is correct

  @account_credit_control_mark
  Scenario: mark lines
    Given there is "draft" credit lines
    And I mark all draft email to state "to_be_sent"
    Then the draft line should be in state "to_be_sent"

  @account_credit_control_run_month
  Scenario: Create run
    Given I need a "credit.control.run" with oid: credit_control.run6
    And having:
      | name |      value |
      | date | 2013-06-30 |
    When I launch the credit run
    Then my credit run should be in state "done"
    And the generated credit lines should have the following values:
     | balance |   date due | account     | policy        |       date | partner        | channel | level | move line | policy level          | state | amount due | currency |
     |    1200 | 2013-03-31 | Debtors     | 2 time policy | 2013-06-30 | customer_2     | letter  |     2 | SI_5      | 60 days last reminder | draft |       1200 | USD      |
     |    1200 | 2013-03-17 | Debtors     | 2 time policy | 2013-06-30 | customer_3     | letter  |     2 | SI_8      | 60 days last reminder | draft |       1200 | USD      |
     | 1050.01 | 2013-04-30 | Debtors     | 3 time policy | 2013-06-30 | customer_4     | email   |     2 | SI_12     | 30 days end of month  | draft |    1050.01 | USD      |
     |     840 | 2013-03-31 | Debtors     | 3 time policy | 2013-06-30 | customer_4     | letter  |     3 | SI_11     | 10 days last reminder | draft |        840 | USD      |
     |    1500 | 2013-04-14 | Debtors USD | 3 time policy | 2013-06-30 | customer_5_usd | letter  |     3 | SI_15     | 10 days last reminder | draft |       1500 | USD      |
     |     500 | 2013-04-14 | Debtors     | 3 time policy | 2013-06-30 | Scrooge McDuck | letter  |     3 | SI_17     | 10 days last reminder | draft |       1500 |          |
     |    1050 | 2013-04-30 | Debtors     | 3 time policy | 2013-06-30 | Donald Duck    | email   |     2 | SI_18     | 30 days end of month  | draft |       1050 |          |
     |    1050 | 2013-04-30 | Debtors     | 3 time policy | 2013-06-30 | Gus Goose      | email   |     2 | SI_19     | 30 days end of month  | draft |       1050 |          |
