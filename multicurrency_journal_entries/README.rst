.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Multicurrency Journal Entries
=============================

This module was written to extend the functionality of the e-invoicing module
(account) in order to be able to create journal entries in a currency different
than the currency of the company

Installation
============

To install this module, you need to:

* clone the branch 8.0 of the repository https://github.com/OCA/account-financial-tools
* add the path to this repository in your configuration (addons-path)
* update the module list
* search for "Multicurrency Journal Entries" in your addons
* install the module

Configuration
=============

The currency rate need to be set. You can use the module "Currency Rate Update"
for that. It is also an OCA module accessible here:
https://github.com/OCA/account-financial-tools
In the module Settings/ Configuration/ Invoicing, you need to tick the box
"Allow multi currencies" to be able to select a currency on the account move
lines (Journal Entries).

Usage
=====

When you will create a journal entry, at the entry lines level, you can enter
an amount in a currency you have selected.
This amount will populate the debit field if it is positive and the credit
field value if it is negative according to the currency rate of the date of
the transaction.

Main Features
-------------

* The conversion of the currency amount to the currency of the company in the
debit and credit move lines.


Credits
=======

Contributors
------------

* Matt Choplin choplin.mat@gmail.com


Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
