# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Move Line Sale Info",
    "summary": "Introduces the purchase order line to the journal items",
    "version": "14.0.1.0.2",
    "author": "ForgeFlow S.L., " "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Generic",
    "depends": [
        "account_move_line_stock_info",
        "sale_stock",
        "stock_account_prepare_anglo_saxon_out_lines_hook",
    ],
    "license": "AGPL-3",
    "data": ["security/account_security.xml", "views/account_move_view.xml"],
    "installable": True,
    "post_init_hook": "post_init_hook",
}
