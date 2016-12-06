.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=============
Check Deposit
=============

This module allows you to easily manage check deposits : you can select all
the checks you received and create a global deposit for the
selected checks. This module supports multi-currency ; each deposit has a currency
and all the checks of the deposit must have the same currency
(so, if you have checks in EUR and checks in USD, you must create 2 deposits :
one in EUR and one in USD).

Configuration
=============

In the menu *Accounting > Configuration > Accounting > Journals*, create a new journal:

* Name: Checks Received
* Type: Bank
* Short Code: CHK (or any code you want)
* Default Debit Account: select an account for checks received
* Default Credit Account: idem

This bank journal will be available as a payment method in Odoo. The account you configured as *Default Debit Account* and *Defaut Credit Account* is the account via which the amounts of checks will transit between the reception of a check from a customer and the validation of the check deposit in Odoo.

On the Settings page of the Accounting, you should configure the *Check Deposit Offsetting Account*:

* if you select *Bank Account*, the counter-part of the account move related to the check deposit will be the default debit account of the bank account selected on the check deposit.
* if you select *Transfer Account*, you will have to select a specific account that will be used as transfer account for check deposits.

Usage
=====

When you receive a check that pays a customer invoice, you can go to that invoice and click on the button *Register Payment* and select the *Check Received* journal as *Payment Method*.

When you want to deposit checks to the bank, go to the menu *Accounting > Adviser > Check Deposit*, create a new check deposit and set the journal *Checks Received* and select the bank account on which you want to credit the checks. Then click on *Add an item* to select the checks you want to deposit at the bank. Eventually, validate the deposit and print the report (you probably want to customize this report).

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/10.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-financial-tools/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Benoît GUILLOT <benoit.guillot@akretion.com>
* Chafique DELLI <chafique.delli@akretion.com>
* Alexis de Lattre <alexis.delattre@akretion.com>
* Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
