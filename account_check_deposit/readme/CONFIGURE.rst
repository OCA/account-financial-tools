In the menu *Invoicing > Configuration > Accounting > Journals*, create a new
journal:

* Name: Checks Received
* Type: Bank
* Short Code: CHK (or any code you want)
* Default Debit Account: select an account for checks received
* Default Credit Account: idem

This bank journal will be available as a payment method in Odoo. The account
you configured as *Default Debit Account* and *Defaut Credit Account* is the
account via which the amounts of checks will transit between the reception of a
check from a customer and the validation of the check deposit in Odoo.

On the Settings page of the Accounting, you should configure the
*Check Deposit Offsetting Account*:

* if you select *Bank Account*, the counter-part of the account move related to
  the check deposit will be the default debit account of the bank account
  selected on the check deposit.
* if you select *Transfer Account*, you will have to select a specific account
  that will be used as transfer account for check deposits.
