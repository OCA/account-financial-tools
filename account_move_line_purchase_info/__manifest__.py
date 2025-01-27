# Copyright 2019-2020 ForgeFlow S.L.
#   (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Move Line Purchase Info",
    "summary": "Introduces the purchase order line to the journal items",
    "version": "17.0.2.0.0",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Generic",
    "depends": ["purchase_stock", "base_view_inheritance_extension"],
    "license": "AGPL-3",
    "data": [
        "security/account_security.xml",
        "views/account_move_view.xml",
        "views/purchase_order_view.xml",
    ],
    "installable": True,
}
