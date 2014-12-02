###############################################################################
#
#    OERPScenario, OpenERP Functional Tests
#    Copyright 2012-2014 Camptocamp SA
#    Author Nicolas Bessi
##############################################################################

# Features Generic tags (none for all)
##############################################################################

@account_credit_control @account_credit_control_run  @account_credit_control_run_may

Feature: Ensure that email credit line generation first pass is correct

  @account_credit_control_mark
  Scenario: mark lines
    Given there is "draft" credit lines
    And I mark all draft email to state "to_be_sent"
    Then the draft line should be in state "to_be_sent"

 @pay_invoice_si_16
  Scenario: I pay entirely the invoice SI 16, so it should no longer appear in the credit control lines
    Given I pay the full amount on the invoice "SI_16"
    Then My invoice "SI_16" is in state "paid" reconciled with a residual amount of "0.0"

  @pay_invoice_si_17
  Scenario: I pay entirely the invoice SI 17, so it should no longer appear in the credit control lines
    Given I pay 1000.0 on the invoice "SI_17"
    Then My invoice "SI_17" is in state "open" reconciled with a residual amount of "500.0"

  @pay_invoice_si_18_part1
  Scenario: I pay the first part of the invoice SI 18, so it should no longer appear in the credit control lines however, the second move lines should still appears
    Given I pay 450.0 on the invoice "SI_18"
    Then My invoice "SI_18" is in state "open" reconciled with a residual amount of "1050.0"

  @account_credit_control_run_month
  Scenario: Create run
    Given I need a "credit.control.run" with oid: credit_control.run5
    And having:
      | name |      value |
      | date | 2013-05-31 |
    When I launch the credit run
    Then my credit run should be in state "done"
    And the generated credit lines should have the following values:
     | balance |   date due | account     | policy        |       date | partner        | channel | level | move line | policy level          | state | amount due | currency |
     |    1500 | 2013-04-30 | Debtors     | 2 time policy | 2013-05-31 | customer_2     | email   |     1 | SI_6      | 30 days end of month  | draft |       1500 | USD      |
     |    1000 | 2013-02-28 | Debtors     | 2 time policy | 2013-05-31 | customer_2     | letter  |     2 | SI_4      | 60 days last reminder | draft |       1000 |          |
     |    1000 | 2013-02-17 | Debtors     | 2 time policy | 2013-05-31 | customer_3     | letter  |     2 | SI_7      | 60 days last reminder | draft |       1000 |          |
     |    1500 | 2013-04-14 | Debtors     | 2 time policy | 2013-05-31 | customer_3     | email   |     1 | SI_9      | 30 days end of month  | draft |       1500 |          |
     |     840 | 2013-03-31 | Debtors     | 3 time policy | 2013-05-31 | customer_4     | email   |     2 | SI_11     | 30 days end of month  | draft |        840 | USD      |
     |    1500 | 2013-04-14 | Debtors USD | 3 time policy | 2013-05-31 | customer_5_usd | email   |     2 | SI_15     | 30 days end of month  | draft |       1500 | USD      |
     |     700 | 2013-02-28 | Debtors     | 3 time policy | 2013-05-31 | customer_4     | letter  |     3 | SI_10     | 10 days last reminder | draft |        700 |          |
     |  449.99 | 2013-03-15 | Debtors     | 3 time policy | 2013-05-31 | customer_4     | letter  |     3 | SI_12     | 10 days last reminder | draft |     449.99 | USD      |
     | 1050.01 | 2013-04-30 | Debtors     | 3 time policy | 2013-05-31 | customer_4     | email   |     1 | SI_12     | 10 days net           | draft |    1050.01 | USD      |
     |    1200 | 2013-03-17 | Debtors USD | 3 time policy | 2013-05-31 | customer_5_usd | letter  |     3 | SI_14     | 10 days last reminder | draft |       1200 | USD      |
     |     500 | 2013-04-14 | Debtors     | 3 time policy | 2013-05-31 | Scrooge McDuck | email   |     2 | SI_17     | 30 days end of month  | draft |       1500 |          |
     |    1050 | 2013-04-30 | Debtors     | 3 time policy | 2013-05-31 | Donald Duck    | email   |     1 | SI_18     | 10 days net           | draft |       1050 |          |
     |     150 | 2013-03-15 | Debtors     | 3 time policy | 2013-05-31 | Gus Goose      | letter  |     3 | SI_19     | 10 days last reminder | draft |        450 |          |
     |    1050 | 2013-04-30 | Debtors     | 3 time policy | 2013-05-31 | Gus Goose      | email   |     1 | SI_19     | 10 days net           | draft |       1050 |          |
