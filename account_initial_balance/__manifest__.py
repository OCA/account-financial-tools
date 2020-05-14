# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Manage initial balance",
    "version": "11.0.1.0.0",
    "depends": ["stock", "sale", "purchase", "account"],
    'author': "Rosen Vladimirov, Bioprint Ltd.,",
    "website": 'https://github.com/rosenvladimirov/account-financial-tools',
    "category": "Finance",
    "data": [
        "data/ir_module_account_initial_balance.xml",
        "security/account_recalculate_stock_move.xml",
        "views/stock_account_views.xml",
        "views/purchase_views.xml",
        "views/sale_views.xml",
    ],
    'license': 'AGPL-3',
    "auto_install": False,
    'installable': True,
}
