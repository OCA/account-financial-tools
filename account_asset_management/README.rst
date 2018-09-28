.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

==========================
Financial asset management
==========================

This Module manages the assets owned by a company. It will keep
track of depreciation's occurred on those assets. And it allows to create
accounting entries from the depreciation lines.

The full asset life-cycle is managed (from asset creation to asset removal).

Assets can be created manually as well as automatically
(via the creation of an accounting entry on the asset account).

Excel based reporting is available via the 'account_asset_management_xls' module.

The module contains a large number of functional enhancements compared to
the standard account_asset module from Odoo.

Configuration
=============

It is recommended to configure your Purchase Journal with "Group Invoice Lines" to avoid the
creation of separate assets per Supplier Invoice Line.

Usage
=====

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/10.0

Known issues
============

The module in NOT compatible with the standard account_asset module.

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
- OpenERP SA
- Luc De Meyer (Noviat)
- Frédéric Clementi (camptocamp)
- Florian Dacosta (Akretion)
- Stéphane Bidoul (Acsone)
- Adrien Peiffer (Acsone)

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
