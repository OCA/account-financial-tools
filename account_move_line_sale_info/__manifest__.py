# Copyright 2020-23 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Move Line Sale Info",
    "summary": "Introduces the purchase order line to the journal items",
    "version": "19.0.1.0.0",
    "author": "ForgeFlow S.L., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Generic",
    "depends": ["sale_stock", "stock_account"],
    "license": "AGPL-3",
    "data": ["security/account_security.xml", "views/account_move_view.xml"],
    "installable": True,
}
