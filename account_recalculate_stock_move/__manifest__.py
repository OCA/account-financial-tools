# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Re-booking The Stock Move",
    "version": "11.0.1.0.0",
    "depends": ["stock", "stock_account", "sale", "sale_stock", "purchase"],
    'author': "Rosen Vladimirov, Bioprint Ltd.,",
    "website": 'https://github.com/rosenvladimirov/account-financial-tools',
    "category": "Finance",
    "data": [
        "views/stock_account_views.xml",
        "views/sale_views.xml",
        "views/purchase_views.xml",
        "wizard/create_transfer.xml",
    ],
    'license': 'AGPL-3',
    "auto_install": False,
    'installable': True,
}
