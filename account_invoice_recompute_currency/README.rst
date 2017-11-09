.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

==================================
Update currency of Account Invoice
==================================

This module allows users to update the currency of Invoices (in draft state) by wizard.
After update to new currency, all the unit prices of invoice lines will be recomputed
to new currency, thus the Total amounts (tax and without tax) of Invoice will be in the new currency also

Configuration
=============

The exchange rate will be configured in
Accounting > Configuration > Multi-Currencies > Currencies

Usage
=====
To use this module, the user must be in group Accounting & Finance / Adviser
to be able to update currency of Invoices

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-financial-tools/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://odoo-community.org/logo.png>`_.

Contributors
------------

* Duc, Dao Dong <duc.dd@komit-consulting.com> (https://komit-consulting.com)


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
