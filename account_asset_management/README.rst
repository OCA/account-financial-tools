Financial asset management.
===========================

This Module manages the assets owned by a company. It will keep
track of depreciation's occurred on those assets. And it allows to create
accounting entries from the depreciation lines.

The full asset life-cycle is managed (from asset creation to asset removal).

Assets can be created manually as well as automatically
(via the creation of an accounting entry on the asset account).

Excel based reporting is available via the 'account_asset_management_xls' module.

The module contains a large number of functional enhancements compared to
the standard account_asset module from Odoo.

Known issues
------------

The module in NOT compatible with the standard account_asset module.

Configuration Tips
------------------

- It is recommended to configure your Purchase Journal with "Group Invoice Lines" to avoid the
  creation of separate assets per Supplier Invoice Line.

Contributors
------------
- OpenERP SA
- Luc De Meyer (Noviat)
- Frédéric Clementi (camptocamp)
- Florian Dacosta (Akretion)
- Stéphane Bidoul (Acsone)

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose mission is to support the collaborative development of Odoo features and promote its widespread use.
