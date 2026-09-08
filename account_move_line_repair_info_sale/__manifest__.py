# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Move Line Repair Info Sale",
    "summary": "Introduces the repair order to the journal items of sales invoices",
    "version": "19.0.1.0.0",
    "author": "ForgeFlow S.L., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Generic",
    "depends": [
        "account_move_line_repair_info",
        "sale_stock",
    ],
    "license": "AGPL-3",
    "installable": True,
    "post_init_hook": "post_init_hook",
}
