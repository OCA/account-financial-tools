In the menu *Invoicing > Configuration > Accounting > Journals*, create a new
journal:

* Name: Checks Received
* Type: Bank
* Short Code: CHK (or any code you want)
* Outstanding Receipts Account: select an account for checks received

Note that, on this *Checks Received* journal, the bank account and suspense account will not be used, so don't worry about these parameters.

This bank journal will be available as a payment method in Odoo. The account
you configured as *Outstanding Receipts Account* is the
account via which the amounts of checks will transit between the reception of a
check from a customer and the validation of the check deposit in Odoo.

When you validate the check deposit in Odoo, it will generate a new journal entry that will move the amounts from the *Outstanding Receipts Account* of the checks received journal to the *Outstanding Receipts Account* of the bank journal related to the check deposit. It will also reconcile in the *Outstanding Receipts Account* of the checks received journal.
