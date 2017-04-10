.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==================================
Link between assets and equipments
==================================

This module links assets with equipments, allowing to create automatically
an equipment from the supplier invoice if an equipment category is assigned
in the asset category.

Configuration
=============

To configure this module, you need to:

#. Go to *Accounting > Configuration > Management > Asset Types*.
#. Select one asset type.
#. Fill the field "Equipment category" with the equipment category we want to
   assign to the auto-created equipments.

Usage
=====

To use this module, you need to:

#. Go to *Accounting > Purchases > Vendor Bills*.
#. Create a new bill.
#. Create one invoice line.
#. Select an asset category with an equipment category filled.
#. Validate the invoice.
#. A new page called "Equipments" will appear with the auto-created equipments.
#. An equipment will created per each quantity indicated in the invoice line.
#. If the quantity is not integer (for example: 3.5), the upper integer number
   will be used (4 for the example).
#. If you cancel the bill, the created equipments will be removed.

You can access equipments for the created asset:

#. Go to *Accounting > Adviser > Assets*.
#. Open the created asset
#. You will see an smart-button with the string "Equipments" that links to the
   created asset.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/10.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-financial-tools/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Pedro M. Baeza <pedro.baeza@tecnativa.com>

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
