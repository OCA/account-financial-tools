###############################################################################
#
#    OERPScenario, OpenERP Functional Tests
#    Copyright 2012-2014 Camptocamp SA
#    Author Nicolas Bessi
##############################################################################

# Features Generic tags (none for all)
##############################################################################

@account_credit_control @account_credit_control_run  @account_credit_control_run_mar

Feature: Ensure that email credit line generation first pass is correct

  @account_credit_control_mark
  Scenario: mark lines
    Given there is "draft" credit lines
    And I mark all draft email to state "to_be_sent"
    Then the draft line should be in state "to_be_sent"

  @pay_invoice_si_19_part1
  Scenario: I pay a part of the first part of the invoice SI 19,
    Given I pay 300.0 on the invoice "SI_19"
    Then My invoice "SI_19" is in state "open" reconciled with a residual amount of "1200.0"

  @account_credit_control_run_month_mar
  Scenario: Create run
    Given I need a "credit.control.run" with oid: credit_control.run3
    And having:
      | name |      value |
      | date | 2013-03-31 |
    When I launch the credit run
    Then my credit run should be in state "done"
    And the generated credit lines should have the following values:
     | balance |   date due | account     | policy        |       date | partner        | channel | level | move line | policy level          | state | amount due | currency |
     |    1000 | 2013-02-28 | Debtors     | 2 time policy | 2013-03-31 | customer_2     | email   |     1 | SI_4      | 30 days end of month  | draft |       1000 |          |
     |    1000 | 2013-02-17 | Debtors     | 2 time policy | 2013-03-31 | customer_3     | email   |     1 | SI_7      | 30 days end of month  | draft |       1000 |          |
     |     700 | 2013-02-28 | Debtors     | 3 time policy | 2013-03-31 | customer_4     | email   |     1 | SI_10     | 10 days net           | draft |        700 |          |
     |  449.99 | 2013-03-15 | Debtors     | 3 time policy | 2013-03-31 | customer_4     | email   |     1 | SI_12     | 10 days net           | draft |     449.99 | USD      |
     |    1200 | 2013-03-17 | Debtors USD | 3 time policy | 2013-03-31 | customer_5_usd | email   |     1 | SI_14     | 10 days net           | draft |       1200 | USD      |
     |     360 | 2013-02-15 | Debtors     | 3 time policy | 2013-03-31 | customer_4     | email   |     2 | SI_11     | 30 days end of month  | draft |        360 | USD      |
     |    1000 | 2013-02-17 | Debtors USD | 3 time policy | 2013-03-31 | customer_5_usd | email   |     2 | SI_13     | 30 days end of month  | draft |       1000 | USD      |
     |     300 | 2013-01-18 | Debtors     | 3 time policy | 2013-03-31 | customer_4     | letter  |     3 | SI_10     | 10 days last reminder | draft |        300 |          |
     |     450 | 2013-03-15 | Debtors     | 3 time policy | 2013-03-31 | Donald Duck    | email   |     1 | SI_18     | 10 days net           | draft |        450 |          |
     |     150 | 2013-03-15 | Debtors     | 3 time policy | 2013-03-31 | Gus Goose      | email   |     1 | SI_19     | 10 days net           | draft |        450 |          |
