.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

===================================
Optional validation of VAT via VIES
===================================

This module extends base_vat module features, allowing theses use cases:
- Mark when a VAT is VIES validated
- Set a VAT without country preffix when no VIES validation passed
- Set a VAT from a country with no validation method without preffix EU

For some customers is important to see in invoices its VAT ID without any extra
preffix.


Installation
============

To install this module, you need vatnumber python library:

* pip install vatnumber


Configuration
=============

In order to activate VIES validation, you must set this option in your company:
Settings > Companies > Companies > Your Company > Configuration > Accounting > VIES VAT Check

If this option is activated, when VAT is validated against VIES service, then
"VIES validation passed" field will be True. If VAT is not validated against
VIES service, then will be validate against country validation method and
"VIES validation passed" field will be False

If this option is deactivated, then "VIES validation passed" will be always False


Usage
=====

Here we have some real use cases:

A. German steuernummer
----------------------

In Germany some customers has not VAT ID, but only German Steuernummer. There is not
validation method for this king of identifiers, but we want to show it in our invoice

* Fill TIN field with german steuernummer, with no extra preffix
* Let VAT Country field empty (no validation available)
* Save

Odoo will save TIN number with no validation and the SteuerNummer will appear
in customer invoice.

B. TIN number from country with no validation
---------------------------------------------

Some countries has no validation method (actually only 41 of 253 have) but
our customer wants its TIN number in its invoice without any extra preffix

* Fill TIN field with customer TIN number, with no extra preffix
* Let VAT Country field empty (no validation available)
* Save

Odoo will save TIN number with no validation and the number will appear
in customer invoice without any extra preffix.

C. TIN number from country with validation method but not in VIES database
--------------------------------------------------------------------------

Some customers has a TIN from a country with validation method but they wants
its TIN number in its invoice without any extra preffix. We want to validate
TIN number to be sure there is no mistake

* Fill TIN field with customer TIN number, with no extra preffix
* Set VAT Country field
* Save

Odoo will save TIN number only if TIN number pass selected country validation
method, showing a Warning if not. TIN number will appear in customer invoice
without any extra preffix.

If VIES validation is activated, Odoo will try to validate against VIES database
first and validation will no passed, so Odoo will try with country validation and
"VIES validation passed" field will be False

D. TIN number from country with validation method and in VIES database
----------------------------------------------------------------------

This is the common case for Odoo standard. So if wehave VIES validation activated:

* Fill TIN field with customer VAT ID, with country preffix
* Let VAT Country field empty
* Save

Odoo will validate TIN number against VIES, save TIN number, set VAT Country
properly and set "VIES validation passed" as True. TIN number will appear in
customer invoice with country preffix.


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/account-financial-tools/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/account-financial-tools/issues/new?body=module:%20vat_optional_vies%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


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
