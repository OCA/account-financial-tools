.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Credit Control Lawsuit
======================

Extends the credit control with the possibility to generate lawsuit
requisitions when all levels were reached.

Overview:

* Adds **Lawsuit offices** (where the lawsuit can be filed).
* The Lawsuit offices have a **Fees Schedule**, with progressive fees
  depending on the due amount.
* Lawsuit offices are linked to one or many zip codes.
* A partner is automatically assigned to the lawsuit office in the same
  city and zip.
* When a credit control level implies a lawsuit procedure, a new
  printed document can be generated on the invoice for the lawsuit
  requisition.

Configuration
=============

Create **Fees Schedules** in ``Invoicing > Configuration > Credit Control >
Fees Schedules``. A fees schedule defines how much fees the lawsuit
will cost depending on the amount still unpaid by the customer.

Then, create the **Lawsuit Offices** in ``Invoicing > Configuration >
Credit Control > Lawsuit Offices``. An office needs an address, a **Fees
Schedule** and one or several zip where the office is active.

Add a new level in the **Credit Control policy** in ``Invoicing >
Configuration > Credit Control > Credit Control Policies``. This level
must have the check box **Needs a Lawsuit procedure** activated.

Usage
=====

Select the invoices that needs a lawsuit requisition and use the menu
action ``More > Print Lawsuit Requisition``. The invoices that don't need
a lawsuit requisition will be filtered out of the list.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/account-financial-tools/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/account-financial-tools/issues/new?body=module:%20account_credit_control_lawsuit%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Nicolas Bessi <nicolas.bessi@camptocamp.com>
* Guewen Baconnier <guewen.baconnier@camptocamp.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
