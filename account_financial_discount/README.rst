==========================
Account Financial Discount
==========================

This module adds functionality to handle financial discounts for early payments,
and to generate proper write-offs during reconciliation.

Configure
=========

Go to Accounting > Configuration > Payment Terms, to define a payment term
involving a financial discount:

* Set a number of days while discount is available after posting
* Set a discount percentage

Go to Accounting > Configuration > Reconciliation models, to define a
reconciliation model applying financial discount.

* Set write-off accounts for expenses and revenues
* Set a label for write-off line
* Set a tolerance to apply discount (e.g. 0.05 for 5 cts)

Usage
=====

When a payment term with discount is selected on an invoice (i.e Customers
invoices or Vendor bills), the available discount will be stored on the first
payment term line once the invoice is posted.

The financial discount will then be applied during the reconciliation process
if the payment is done before the discount date, or if the "Force financial discount"
is used on the invoice.

Limitations
===========

* Storage of available discount is only done if the invoice doesn't include
  more than one account.tax.
* Tax write-off is only done automatically using bank statement reconciliation
  and not when doing manual payments.
* On payment term having multiple term lines, financial discount will be applied
  even if the statement amount covers only first payment term line
* Financial discount cannot be applied if the payment is done in another
  currency than the invoice.
