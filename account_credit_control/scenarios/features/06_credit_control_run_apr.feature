###############################################################################
#
#    OERPScenario, OpenERP Functional Tests
#    Copyright 2012-2014 Camptocamp SA
#    Author Nicolas Bessi
##############################################################################

# Features Generic tags (none for all)
##############################################################################

@account_credit_control @account_credit_control_run  @account_credit_control_run_apr

Feature: Ensure that email credit line generation first pass is correct

    @account_credit_control_mark
  Scenario: mark lines
    Given there is "draft" credit lines
    And I mark all draft email to state "to_be_sent"
    Then the draft line should be in state "to_be_sent"

  @account_credit_control_run_month
  Scenario: Create run
    Given I need a "credit.control.run" with oid: credit_control.run4
    And having:
      | name | value    |
      | date | 2013-04-30 |

    When I launch the credit run
    Then my credit run should be in state "done"
    And the generated credit lines should have the following values:
     | balance |   date due | account     | policy        |       date | partner        | channel | level | move line | policy level          | state | amount due | currency |
     |     360 | 2013-02-15 | Debtors     | 3 time policy | 2013-04-30 | customer_4     | letter  |     3 | SI_11     | 10 days last reminder | draft |        360 | USD      |
     |    1200 | 2013-03-31 | Debtors     | 2 time policy | 2013-04-30 | customer_2     | email   |     1 | SI_5      | 30 days end of month  | draft |       1200 | USD      |
     |    1200 | 2013-03-17 | Debtors     | 2 time policy | 2013-04-30 | customer_3     | email   |     1 | SI_8      | 30 days end of month  | draft |       1200 | USD      |
     |     700 | 2013-02-28 | Debtors     | 3 time policy | 2013-04-30 | customer_4     | email   |     2 | SI_10     | 30 days end of month  | draft |        700 |          |
     |     840 | 2013-03-31 | Debtors     | 3 time policy | 2013-04-30 | customer_4     | email   |     1 | SI_11     | 10 days net           | draft |        840 | USD      |
     |  449.99 | 2013-03-15 | Debtors     | 3 time policy | 2013-04-30 | customer_4     | email   |     2 | SI_12     | 30 days end of month  | draft |     449.99 | USD      |
     |    1500 | 2013-04-14 | Debtors USD | 3 time policy | 2013-04-30 | customer_5_usd | email   |     1 | SI_15     | 10 days net           | draft |       1500 | USD      |
     |    1200 | 2013-03-17 | Debtors USD | 3 time policy | 2013-04-30 | customer_5_usd | email   |     2 | SI_14     | 30 days end of month  | draft |       1200 | USD      |
     |    1500 | 2013-04-14 | Debtors USD | 3 time policy | 2013-04-30 | customer_5_usd | email   |     1 | SI_15     | 10 days net           | draft |       1500 | USD      |
     |    1500 | 2013-04-14 | Debtors     | 3 time policy | 2013-04-30 | customer_4     | email   |     1 | SI_16     | 10 days net           | draft |       1500 |          |
     |    1500 | 2013-04-14 | Debtors     | 3 time policy | 2013-04-30 | Scrooge McDuck | email   |     1 | SI_17     | 10 days net           | draft |       1500 |          |
     |     450 | 2013-03-15 | Debtors     | 3 time policy | 2013-04-30 | Donald Duck    | email   |     2 | SI_18     | 30 days end of month  | draft |        450 |          |
     |     150 | 2013-03-15 | Debtors     | 3 time policy | 2013-04-30 | Gus Goose      | email   |     2 | SI_19     | 30 days end of month  | draft |        450 |          |
