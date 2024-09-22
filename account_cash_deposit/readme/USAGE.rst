To create a new cash **deposit**, go to the menu *Invoicing > Accounting > Miscellaneous > Cash Deposits* and click on *Create*: select the currency, the cash box from which you will take the cash out and the bank journal corresponding to the bank account on which you want to deposit the cash. Then create/edit lines to enter the quantity for each kind of bank note and coin rolls. Then, you can print a PDF report designed to be a kind of delivery report for the cash. Upon validation, Odoo will generate a journal entry in the cash journal that:

* credits the cash account,
* debits the inter-banks transfer account.

.. figure:: static/description/cash_deposit_form.png
   :scale: 100 %
   :alt: Cash Deposit form view

The process is very similar when **ordering** cash but you have to use another menu entry: menu *Invoicing > Accounting > Miscellaneous > Cash Orders*. Select the currency, the cash box that will receive the cash and the bank account from which the bank will take the money. Create/edit lines to enter the details of your order (bank notes, coin rolls). Then, you can confirm the order and print a PDF report designed to be sent to your bank as a cash order. Eventually, when the bank delivers the cash to you, you should validate the cash order and Odoo will generate a journal entry in the cash journal that:

* debits the cash account,
* credits the inter-banks transfer account.
