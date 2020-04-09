# Copyright 2019-2020 ForgeFlow S.L.
#   (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Move Line Purchase Info",
    "summary": "Introduces the purchase order line to the journal items",
    "version": "13.0.1.1.0",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://www.github.com/OCA/account-financial-tools",
    "category": "Generic",
    "depends": ["purchase_stock"],
    "license": "AGPL-3",
    "data": ["security/account_security.xml", "views/account_move_view.xml"],
    "installable": True,
}
