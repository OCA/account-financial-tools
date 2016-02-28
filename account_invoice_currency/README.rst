.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

====================================
Account invoices in company currency
====================================

This module adds functional fields to show invoices in the company currency:
amount untaxed, amount taxed and amount total.

These fields are shown in "Other information" tab in invoice form.


Usage
=====

**NOTE #1**: Amount untaxed and amount total are official account fields in v9.
This addon adds amount taxes and shows all of them in invoice form.

**NOTE #2**: Please note that these fields are negative (as done in v9 account addon)
for credit notes (for example a refund invoice)


Known issues / Roadmap
======================

These fields name change from v8:

* cc_amount_untaxed -> amount_untaxed_signed (already in account v9)
* cc_amount_tax -> amount_tax_signed (added by this addon)
* cc_amount_total -> amount_total_company_signed (already in account v9)


.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/9.0


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

* Jordi Esteve <jesteve@zikzakmedia.com>
* Joaquín Gutierrez <joaquing.pedrosa@gmail.com>
* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
* Antonio Espinosa <antonio.espinosa@tecnativa.com>

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
