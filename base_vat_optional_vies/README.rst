.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

===================================
Optional validation of VAT via VIES
===================================

This module extends base_vat module features allowing to know if VIES
validation was passed or not.

Then you can use "VIES validation passed" field in order to show VAT ID with
or without country preffix in invoices, for instance.

*NOTE*: Although VIES validation is set in your company, this validation
will not block VAT ID write (main difference to Odoo standard behavior) if this
VAT ID is valid in its country.

Configuration
=============

In order to activate VIES validation, you must set this option in your company:
Settings > Companies > Your Company > VIES VAT Check

Usage
=====

When VIES VAT Check is activated:

* Odoo will try to validate VAT against VIES online service
* If passed, then "VIES validation passed" field will be True
* If not passed, then try to validate using country validation method
* If validated, then "VIES validation passed" field will be False
* If not validated, then a ValidationError will be shown to user

When VIES VAT Check is not activated:

* "VIES validation passed" field will be always False

You must prefix VAT with country code (ISO 3166-1 alpha-2) and if you want to
bypass country validation you can use "EU" code

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/10.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-financial-tools/issues>`_. In case of trouble,
please check there if your issue has already been reported. If you spotted it
first, help us smash it by providing detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Rafael Blasco <rafael.blasco@tecnativa.com>
* Antonio Espinosa <antonio.espinosa@tecnativa.com>
* Sergio Teruel <sergio.teruel@tecnativa.com>
* David Vidal <david.vidal@tecnativa.com>

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
