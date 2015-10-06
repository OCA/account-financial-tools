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

*NOTE*: Altought VIES validation is actived in your company, this validation
will not block VAT ID write (main different to Odoo standard behavior) if this
VAT ID is valid in its country.


Configuration
=============

In order to activate VIES validation, you must set this option in your company:
Settings > Companies > Companies > Your Company > Configuration > Accounting > VIES VAT Check


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

You must preffix VAT with country code (ISO 3166-1 alpha-2) and if you want to
bypass country validation you can use "EU" code


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/account-financial-tools/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/account-financial-tools/issues/new?body=module:%20base_vat_optional_vies%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Rafael Blasco <rafabn@antiun.com>
* Antonio Espinosa <antonioea@antiun.com>


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
