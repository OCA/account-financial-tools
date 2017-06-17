.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
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
   :target: https://runbot.odoo-community.org/runbot/92/8.0

Known issues
============

The module in NOT compatible with the standard account_asset module.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/{project_repo}/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/{project_repo}/issues/new?body=module:%20{module_name}%0Aversion:%20{version}%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Contributors
------------
- OpenERP SA
- Luc De Meyer (Noviat)
- Frédéric Clementi (camptocamp)
- Florian Dacosta (Akretion)
- Stéphane Bidoul (Acsone)

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
