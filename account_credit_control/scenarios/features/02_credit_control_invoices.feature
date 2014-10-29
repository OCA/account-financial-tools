###############################################################################
#
#    OERPScenario, OpenERP Functional Tests
#    Copyright 2012-2014 Camptocamp SA
#    Author Nicolas Bessi
##############################################################################


@account_credit_control @account_credit_control_setup @account_credit_control_base_data @account_credit_control_invoices

Feature: Invoices creation

##################### Partner 1 ##########################################################

  @inv_1
  Scenario: Create invoice 1

  Given I need a "account.invoice" with oid: scen._inv_1
    And having:
      | name         | value                         |
      | name         | SI_1                          |
      | date_invoice | 2013-01-15                      |
      | partner_id   | by oid: scen.partner_1        |
      | account_id   | by name: Debtors              |
      | journal_id   | by name: Sales                |
      | currency_id  | by name: EUR                  |
      | payment_term | by name: 30 Days End of Month |
      | type         | out_invoice                   |


    Given I need a "account.invoice.line" with oid: scen._inv1_line1
    And having:
      | name       | value               |
      | name       | invoice line 1      |
      | quantity   | 1                   |
      | price_unit | 1000                |
      | account_id | by name: Sales      |
      | invoice_id | by oid: scen._inv_1 |
    Given I find a "account.invoice" with oid: scen._inv_1

    Given I need a "account.invoice.line" with oid: scen._inv1_line2
    And having:
      | name       | value               |
      | name       | invoice line 2      |
      | quantity   | 1                   |
      | price_unit | 1000                |
      | account_id | by name: Sales      |
      | invoice_id | by oid: scen._inv_1 |
    Given I find a "account.invoice" with oid: scen._inv_1
    And I open the credit invoice

  @inv_2
  Scenario: Create invoice 2
  Given I need a "account.invoice" with oid: scen._inv_2
    And having:
      | name         | value                         |
      | name         | SI_2                          |
      | date_invoice | 2013-02-15                      |
      | partner_id   | by oid: scen.partner_1        |
      | account_id   | by name: Debtors              |
      | journal_id   | by name: Sales                |
      | currency_id  | by name: USD                  |
      | payment_term | by name: 30 Days End of Month |
      | type         | out_invoice                   |


    Given I need a "account.invoice.line" with oid: scen._inv2_line1
    And having:
      | name       | value               |
      | name       | invoice line 1      |
      | quantity   | 1                   |
      | price_unit | 1200                |
      | account_id | by name: Sales      |
      | invoice_id | by oid: scen._inv_2 |
    Given I find a "account.invoice" with oid: scen._inv_2
    And I open the credit invoice


  @inv_3
  Scenario: Create invoice 3
  Given I need a "account.invoice" with oid: scen._inv_3
    And having:
      | name         | value                         |
      | name         | SI_3                          |
      | date_invoice | 2013-03-15                      |
      | partner_id   | by oid: scen.partner_1        |
      | account_id   | by name: Debtors              |
      | journal_id   | by name: Sales                |
      | currency_id  | by name: USD                  |
      | payment_term | by name: 30 Days End of Month |
      | type         | out_invoice                   |


    Given I need a "account.invoice.line" with oid: scen._inv3_line1
    And having:
      | name       | value               |
      | name       | invoice line 1      |
      | quantity   | 1                   |
      | price_unit | 1500                |
      | account_id | by name: Sales      |
      | invoice_id | by oid: scen._inv_3 |
    Given I find a "account.invoice" with oid: scen._inv_3
    And I open the credit invoice

##################### Customer 2 ##########################################################

  @inv_4
  Scenario: Create invoice 4

  Given I need a "account.invoice" with oid: scen._inv_4
    And having:
      | name         | value                         |
      | name         | SI_4                          |
      | date_invoice | 2013-01-18                      |
      | partner_id   | by oid: scen.customer_2       |
      | account_id   | by name: Debtors              |
      | journal_id   | by name: Sales                |
      | currency_id  | by name: EUR                  |
      | payment_term | by name: 30 Days End of Month |
      | type         | out_invoice                   |


    Given I need a "account.invoice.line" with oid: scen._inv4_line1
    And having:
      | name       | value               |
      | name       | invoice line 1      |
      | quantity   | 1                   |
      | price_unit | 1000                |
      | account_id | by name: Sales      |
      | invoice_id | by oid: scen._inv_4 |
    Given I find a "account.invoice" with oid: scen._inv_4
    And I open the credit invoice



  @inv_5
  Scenario: Create invoice 5
  Given I need a "account.invoice" with oid: scen._inv_5
    And having:
      | name         | value                         |
      | name         | SI_5                          |
      | date_invoice | 2013-02-15                      |
      | partner_id   | by oid: scen.customer_2       |
      | account_id   | by name: Debtors              |
      | journal_id   | by name: Sales                |
      | currency_id  | by name: USD                  |
      | payment_term | by name: 30 Days End of Month |
      | type         | out_invoice                   |


    Given I need a "account.invoice.line" with oid: scen._inv5_line1
    And having:
      | name       | value               |
      | name       | invoice line 1      |
      | quantity   | 1                   |
      | price_unit | 1200                |
      | account_id | by name: Sales      |
      | invoice_id | by oid: scen._inv_5 |
    Given I find a "account.invoice" with oid: scen._inv_5
    And I open the credit invoice


  @inv_6
  Scenario: Create invoice 6
  Given I need a "account.invoice" with oid: scen._inv_6
    And having:
      | name         | value                         |
      | name         | SI_6                          |
      | date_invoice | 2013-03-15                      |
      | partner_id   | by oid: scen.customer_2       |
      | account_id   | by name: Debtors              |
      | journal_id   | by name: Sales                |
      | currency_id  | by name: USD                  |
      | payment_term | by name: 30 Days End of Month |
      | type         | out_invoice                   |


    Given I need a "account.invoice.line" with oid: scen._inv6_line1
    And having:
      | name       | value               |
      | name       | invoice line 1      |
      | quantity   | 1                   |
      | price_unit | 1500                |
      | account_id | by name: Sales      |
      | invoice_id | by oid: scen._inv_6 |
    Given I find a "account.invoice" with oid: scen._inv_6
    And I open the credit invoice

##################### Customer 3 ##########################################################

  @inv_7
  Scenario: Create invoice 7

  Given I need a "account.invoice" with oid: scen._inv_7
    And having:
      | name         | value                   |
      | name         | SI_7                    |
      | date_invoice | 2013-01-18                |
      | partner_id   | by oid: scen.customer_3 |
      | account_id   | by name: Debtors        |
      | journal_id   | by name: Sales          |
      | currency_id  | by name: EUR            |
      | payment_term | by name: 30 Net Days    |
      | type         | out_invoice             |


    Given I need a "account.invoice.line" with oid: scen._inv7_line1
    And having:
      | name       | value               |
      | name       | invoice line 1      |
      | quantity   | 1                   |
      | price_unit | 1000                |
      | account_id | by name: Sales      |
      | invoice_id | by oid: scen._inv_7 |
    Given I find a "account.invoice" with oid: scen._inv_7
    And I open the credit invoice



  @inv_8
  Scenario: Create invoice 8
  Given I need a "account.invoice" with oid: scen._inv_8
    And having:
      | name         | value                   |
      | name         | SI_8                    |
      | date_invoice | 2013-02-15                |
      | partner_id   | by oid: scen.customer_3 |
      | account_id   | by name: Debtors        |
      | journal_id   | by name: Sales          |
      | currency_id  | by name: USD            |
      | payment_term | by name: 30 Net Days    |
      | type         | out_invoice             |


    Given I need a "account.invoice.line" with oid: scen._inv8_line1
    And having:
      | name       | value               |
      | name       | invoice line 1      |
      | quantity   | 1                   |
      | price_unit | 1200                |
      | account_id | by name: Sales      |
      | invoice_id | by oid: scen._inv_8 |
    Given I find a "account.invoice" with oid: scen._inv_8
    And I open the credit invoice


  @inv_9
  Scenario: Create invoice 9
  Given I need a "account.invoice" with oid: scen._inv_9
    And having:
      | name         | value                   |
      | name         | SI_9                    |
      | date_invoice | 2013-03-15                |
      | partner_id   | by oid: scen.customer_3 |
      | account_id   | by name: Debtors        |
      | journal_id   | by name: Sales          |
      | currency_id  | by name: USD            |
      | payment_term | by name: 30 Net Days    |
      | type         | out_invoice             |


    Given I need a "account.invoice.line" with oid: scen._inv9_line1
    And having:
      | name       | value               |
      | name       | invoice line 1      |
      | quantity   | 1                   |
      | price_unit | 1500                |
      | account_id | by name: Sales      |
      | invoice_id | by oid: scen._inv_9 |
    Given I find a "account.invoice" with oid: scen._inv_9
    And I open the credit invoice

##################### Customer 4 ##########################################################

  @inv_10
  Scenario: Create invoice 10

  Given I need a "account.invoice" with oid: scen._inv_10
    And having:
      | name         | value                            |
      | name         | SI_10                            |
      | date_invoice | 2013-01-18                         |
      | partner_id   | by oid: scen.customer_4          |
      | account_id   | by name: Debtors                 |
      | journal_id   | by name: Sales                   |
      | currency_id  | by name: EUR                     |
      | payment_term | by name: 30% Advance End 30 Days |
      | type         | out_invoice                      |


    Given I need a "account.invoice.line" with oid: scen._inv10_line1
    And having:
      | name       | value                |
      | name       | invoice line 1       |
      | quantity   | 1                    |
      | price_unit | 1000                 |
      | account_id | by name: Sales       |
      | invoice_id | by oid: scen._inv_10 |
    Given I find a "account.invoice" with oid: scen._inv_10
    And I open the credit invoice



  @inv_11
  Scenario: Create invoice 11
  Given I need a "account.invoice" with oid: scen._inv_11
    And having:
      | name         | value                            |
      | name         | SI_11                            |
      | date_invoice | 2013-02-15                         |
      | partner_id   | by oid: scen.customer_4          |
      | account_id   | by name: Debtors                 |
      | journal_id   | by name: Sales                   |
      | currency_id  | by name: USD                     |
      | payment_term | by name: 30% Advance End 30 Days |
      | type         | out_invoice                      |


    Given I need a "account.invoice.line" with oid: scen._inv11_line1
    And having:
      | name       | value                |
      | name       | invoice line 1       |
      | quantity   | 1                    |
      | price_unit | 1200                 |
      | account_id | by name: Sales       |
      | invoice_id | by oid: scen._inv_11 |
    Given I find a "account.invoice" with oid: scen._inv_11
    And I open the credit invoice


  @inv_12
  Scenario: Create invoice 12
  Given I need a "account.invoice" with oid: scen._inv_12
    And having:
      | name         | value                            |
      | name         | SI_12                            |
      | date_invoice | 2013-03-15                         |
      | partner_id   | by oid: scen.customer_4          |
      | account_id   | by name: Debtors                 |
      | journal_id   | by name: Sales                   |
      | currency_id  | by name: USD                     |
      | payment_term | by name: 30% Advance End 30 Days |
      | type         | out_invoice                      |


    Given I need a "account.invoice.line" with oid: scen._inv12_line1
    And having:
      | name       | value                |
      | name       | invoice line 1       |
      | quantity   | 1                    |
      | price_unit | 1500                 |
      | account_id | by name: Sales       |
      | invoice_id | by oid: scen._inv_12 |
    Given I find a "account.invoice" with oid: scen._inv_12
    And I open the credit invoice

##################### Customer 5 ##########################################################

  @inv_13
  Scenario: Create invoice 13

  Given I need a "account.invoice" with oid: scen._inv_13
    And having:
      | name         | value                   |
      | name         | SI_13                   |
      | date_invoice | 2013-01-18                |
      | partner_id   | by oid: scen.customer_5 |
      | account_id   | by name: Debtors USD    |
      | journal_id   | by name: Sales          |
      | currency_id  | by name: USD            |
      | payment_term | by name: 30 Net Days    |
      | type         | out_invoice             |


    Given I need a "account.invoice.line" with oid: scen._inv13_line1
    And having:
      | name       | value                |
      | name       | invoice line 1       |
      | quantity   | 1                    |
      | price_unit | 1000                 |
      | account_id | by name: Sales       |
      | invoice_id | by oid: scen._inv_13 |
    Given I find a "account.invoice" with oid: scen._inv_13
    And I open the credit invoice



  @inv_14
  Scenario: Create invoice 14
  Given I need a "account.invoice" with oid: scen._inv_14
    And having:
      | name         | value                   |
      | name         | SI_14                   |
      | date_invoice | 2013-02-15                |
      | partner_id   | by oid: scen.customer_5 |
      | account_id   | by name: Debtors USD    |
      | journal_id   | by name: Sales          |
      | currency_id  | by name: USD            |
      | payment_term | by name: 30 Net Days    |
      | type         | out_invoice             |


    Given I need a "account.invoice.line" with oid: scen._inv14_line1
    And having:
      | name       | value                |
      | name       | invoice line 1       |
      | quantity   | 1                    |
      | price_unit | 1200                 |
      | account_id | by name: Sales       |
      | invoice_id | by oid: scen._inv_14 |
    Given I find a "account.invoice" with oid: scen._inv_14
    And I open the credit invoice


  @inv_15
  Scenario: Create invoice 15
  Given I need a "account.invoice" with oid: scen._inv_15
    And having:
      | name         | value                   |
      | name         | SI_15                   |
      | date_invoice | 2013-03-15                |
      | partner_id   | by oid: scen.customer_5 |
      | account_id   | by name: Debtors USD    |
      | journal_id   | by name: Sales          |
      | currency_id  | by name: USD            |
      | payment_term | by name: 30 Net Days    |
      | type         | out_invoice             |


    Given I need a "account.invoice.line" with oid: scen._inv15_line1
    And having:
      | name       | value                |
      | name       | invoice line 1       |
      | quantity   | 1                    |
      | price_unit | 1500                 |
      | account_id | by name: Sales       |
      | invoice_id | by oid: scen._inv_15 |
    Given I find a "account.invoice" with oid: scen._inv_15
    And I open the credit invoice

  @inv_16
  Scenario: Create invoice 16
  Given I need a "account.invoice" with oid: scen._inv_16
    And having:
      | name         | value                   |
      | name         | SI_16                   |
      | date_invoice | 2013-03-15                |
      | partner_id   | by oid: scen.customer_4 |
      | account_id   | by name: Debtors        |
      | journal_id   | by name: Sales          |
      | currency_id  | by name: EUR            |
      | payment_term | by name: 30 Net Days    |
      | type         | out_invoice             |

    And I need a "account.invoice.line" with oid: scen._inv16_line1
    And having:
      | name       | value                |
      | name       | invoice line 1       |
      | quantity   | 1                    |
      | price_unit | 1500                 |
      | account_id | by name: Sales       |
      | invoice_id | by oid: scen._inv_16 |
    Then I find a "account.invoice" with oid: scen._inv_16
    And I open the credit invoice

  @inv_17
  Scenario: Create invoice 17
  Given I need a "account.invoice" with oid: scen._inv_17
    And having:
      | name         | value                             |
      | name         | SI_17                             |
      | date_invoice | 2013-03-15                          |
      | partner_id   | by oid: scen.customer_partial_pay |
      | account_id   | by name: Debtors                  |
      | journal_id   | by name: Sales                    |
      | currency_id  | by name: EUR                      |
      | payment_term | by name: 30 Net Days              |
      | type         | out_invoice                       |

    And I need a "account.invoice.line" with oid: scen._inv17_line1
    And having:
      | name       | value                |
      | name       | invoice line 1       |
      | quantity   | 1                    |
      | price_unit | 1500                 |
      | account_id | by name: Sales       |
      | invoice_id | by oid: scen._inv_17 |
    Then I find a "account.invoice" with oid: scen._inv_17
    And I open the credit invoice

  @inv_18
  Scenario: Create invoice 18
  Given I need a "account.invoice" with oid: scen._inv_18
    And having:
      | name         | value                                  |
      | name         | SI_18                                  |
      | date_invoice | 2013-03-15                               |
      | partner_id   | by oid: scen.customer_multiple_payterm |
      | account_id   | by name: Debtors                       |
      | journal_id   | by name: Sales                         |
      | currency_id  | by name: EUR                           |
      | payment_term | by name: 30% Advance End 30 Days       |
      | type         | out_invoice                            |

    And I need a "account.invoice.line" with oid: scen._inv18_line1
    And having:
      | name       | value                |
      | name       | invoice line 1       |
      | quantity   | 1                    |
      | price_unit | 1500                 |
      | account_id | by name: Sales       |
      | invoice_id | by oid: scen._inv_18 |
    Then I find a "account.invoice" with oid: scen._inv_18
    And I open the credit invoice

  @inv_19
  Scenario: Create invoice 19
  Given I need a "account.invoice" with oid: scen._inv_19
    And having:
      | name         | value                                   |
      | name         | SI_19                                   |
      | date_invoice | 2013-03-15                                |
      | partner_id   | by oid: scen.customer_multiple_payterm2 |
      | account_id   | by name: Debtors                        |
      | journal_id   | by name: Sales                          |
      | currency_id  | by name: EUR                            |
      | payment_term | by name: 30% Advance End 30 Days        |
      | type         | out_invoice                             |
    And I need a "account.invoice.line" with oid: scen._inv19_line1
    And having:
      | name       | value                |
      | name       | invoice line 1       |
      | quantity   | 1                    |
      | price_unit | 1500                 |
      | account_id | by name: Sales       |
      | invoice_id | by oid: scen._inv_19 |
    Then I find a "account.invoice" with oid: scen._inv_19
    And I open the credit invoice

  @inv_20
  Scenario: Create invoice 20
  Given I need a "account.invoice" with oid: scen._inv_20
    And having:
      | name         | value                   |
      | name         | SI_20_test_tolerance    |
      | date_invoice | 2013-03-23                |
      | partner_id   | by oid: scen.customer_6 |
      | account_id   | by name: Debtors        |
      | journal_id   | by name: Sales          |
      | currency_id  | by name: EUR            |
      | payment_term | by name: 30 Net Days    |
      | type         | out_invoice             |

    And I need a "account.invoice.line" with oid: scen._inv20_line1
    And having:
      | name       | value                |
      | name       | invoice line 1       |
      | quantity   | 1                    |
      | price_unit | 0.09                 |
      | account_id | by name: Sales       |
      | invoice_id | by oid: scen._inv_20 |
    Then I find a "account.invoice" with oid: scen._inv_20
    And I open the credit invoice

  @inv_20
  Scenario: Create invoice 21 (this receivable account must not be chased-> no credit line creation)
  Given I need a "account.invoice" with oid: scen._inv_21
    And having:
      | name         | value                                  |
      | name         | SI_21_test_receivable_account_excluded |
      | date_invoice | 2013-03-25                               |
      | partner_id   | by oid: scen.customer_6                |
      | account_id   | by name: Debtors GBP                   |
      | journal_id   | by name: Sales                         |
      | currency_id  | by name: EUR                           |
      | payment_term | by name: 30 Net Days                   |
      | type         | out_invoice                            |

    And I need a "account.invoice.line" with oid: scen._inv21_line1
    And having:
      | name       | value                |
      | name       | invoice line 1       |
      | quantity   | 1                    |
      | price_unit | 6666                 |
      | account_id | by name: Sales       |
      | invoice_id | by oid: scen._inv_21 |
    Then I find a "account.invoice" with oid: scen._inv_21
    And I open the credit invoice
