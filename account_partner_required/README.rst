.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

========================
Account Partner Required
========================

This module adds an option *Partner policy* on account types.

You have the choice between 3 policies:

* *optional* (the default policy): partner is optional,
* *always*: require a partner,
* *never*: forbid a partner.

This module is useful to enforce a partner on account move lines on
customer and supplier accounts.

This module is very similar to the module *account_analytic_required* available in the OCA project `account-analytic <https://github.com/OCA/account-analytic>`_.

Configuration
=============

Go to the menu *Accounting > Configuration > Accounting > Account Types* and edit each account types to configure the correct *Partner policy*.

Usage
=====

If you put a partner on an account move line with an account whose type is configured with *Partner policy* = *never*, you will get an error message.

If you don't put a partner on an account move line with an account whose type is configured with *Partner policy* = *always*, you will get an error message.

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

* Stéphane Bidoul <stephane.bidoul@acsone.eu>
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
