.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===================================
Account Invoice Force Currency Rate
===================================

This module allows to select other currency rate than the default one for
invoices that will be invoiced in a different currency than the current
currency of the company.

When selected, that currency rate will be used to generate the accounting entry
for the invoice, this selected rate will be used for make the conversion of the
invoice amount to the current currency of the company.

Usage
=====

To use this module, you need to:

* Go to any draft invoice
* Change the invoice currency
* A default currency rate, based on invoice date and the selected currency
  will be selected by default
* Validate the invoice

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/8.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-financial-tools/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed `feedback
<https://github.com/OCA/
account-financial-tools/issues/new?body=module:%20
account_invoice_force_currency_rate%0Aversion:%20
8.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Ismael Calvo <ismael.calvo@factorlibre.com>
* Hugo Santos <hugo.santos@factorlibre.com>

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