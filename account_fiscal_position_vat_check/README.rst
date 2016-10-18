.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=================================
Account Fiscal Position VAT Check
=================================

With this module, when a user tries to validate a customer invoice or refund
with a fiscal position that requires VAT, Odoo block the validation of the invoice
if the customer doesn't have a VAT number in Odoo.

In the European Union (EU), when an EU company sends an invoice to
another EU company in another country, it can invoice without VAT
(most of the time) but the VAT number of the customer must be displayed
on the invoice.

Configuration
=============

To configure this module, go to *Accounting > Configuration > Accounting
> Fiscal Positions* and enable the option **Customer Must Have VAT number**
on the relevant fiscal positions.

Usage
=====

On the customer form view, Odoo will display a warning when a user sets
a fiscal position that has the option **Customer Must Have VAT number**
on a customer that doesn't have a VAT number yet.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/8.0

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

* Alexis de Lattre <alexis.delattre@akretion.com>

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
