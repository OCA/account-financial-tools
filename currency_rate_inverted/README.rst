.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

===============================
Currency Exchange Rate Inverted
===============================

This module applies the inverse method in the conversion between two currencies.

The inverse method is a calculation method that uses the inverse (reciprocal)
exchange rate for the multiplier and divisor when converting amounts from one
currency to another.

The exchange rate of the multiplier and divisor are the reciprocal,
or opposite, of each other.

The inverse method multiplies the foreign amount by the
exchange rate to calculate the company currency (also called domestic) amount.

Configuration
=============

To convert amounts from one currency to another using the inverse method,
you have to go to 'Accounting / Configuration / Miscellaneous / Currencies'.
Then select the foreign currency that you wish to maintain inversion for
and set the flag 'Inverted exchange rate'.

Usage
=====

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/11.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/{project_repo}/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.


Credits
=======

Images
------

 * Odoo Community Association: `Icon <https://odoo-community.org/logo.png>`_.

Contributors
------------

* Eficent (www.eficent.com)
* Techrifiv Solutions Pte Ltd (www.techrifiv.com.sg)
* Statecraft Systems Pte Ltd (www.statecraftsystems.sg)
* Komit (Jean-Charles Drubay <jc@komit-consulting.com>)

Do not contact contributors directly about support or help with technical issues.

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
