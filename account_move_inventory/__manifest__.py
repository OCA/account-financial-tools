# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Manage account in inventory",
    "version": "11.0.1.0.0",
    "depends": ["stock", "stock_account", "stock_move_location"],
    'author': "Rosen Vladimirov, Bioprint Ltd.,",
    "website": 'https://github.com/rosenvladimirov/account-financial-tools',
    "category": "Finance",
    "data": [
        "views/stock_inventory_views.xml",
        "wizard/stock_move_location.xml",
    ],
    'license': 'AGPL-3',
    "auto_install": False,
    'installable': True,
}
