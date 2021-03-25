# -*- coding: utf-8 -*-
# 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Move Line Sale Info",
    "summary": "Introduces the sale order line to the journal items",
    "version": "10.0.1.0.0",
    "author": "ForgeFlow, "
              "Odoo Community Association (OCA)",
    "website": "http://www.github.com/OCA/account-financial-tools",
    "category": "Generic",
    "depends": ["account_accountant", "account_move_line_stock_info"],
    "license": "AGPL-3",
    "data": [
        "security/account_security.xml",
        "views/account_move_view.xml",
    ],
    'installable': True,
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
}
