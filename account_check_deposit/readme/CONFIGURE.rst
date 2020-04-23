In the menu *Invoicing > Configuration > Accounting > Journals*, create a new journal:

1. **Name:** Checks Received
2. **Type:** Bank
3. **Short Code:** CHK (or any code you want)
4. **Default Debit and Credit Account:** select an account to use for checks received

.. image:: static/description/Configure_chk_received_journal.png

5. DO NOT define a bank account on this journal.

.. image:: static/description/Configure_chk_received_journal_2.png


This bank journal will be available as a payment method in Odoo. 

The accounts you configured as *Default Debit Account* and *Defaut Credit Account* are the accounts via which the amounts of checks will transit between the reception of a check from a customer and the validation of the check deposit in Odoo.

On the Settings page of the Accounting, you should configure the *Check Deposit Offsetting Account*:

* if you select *Bank Account*, the counter-part of the account move related to  the check deposit will be the default debit account of the bank account selected on the check deposit.

* if you select *Transfer Account*, you will have to select a specific account that will be used as transfer account for check deposits.
