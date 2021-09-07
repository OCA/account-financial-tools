# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Manage Valuation Account in product",
    "version": "11.0.1.0.0",
    "depends": [
        "product",
        "stock",
        "stock_account",
    ],
    'author': "Rosen Vladimirov, Bioprint Ltd.,",
    "website": 'https://github.com/rosenvladimirov/account-financial-tools',
    "category": "Finance",
    "data": [
        'views/product_views.xml',
    ],
    'license': 'AGPL-3',
    "auto_install": False,
    'installable': True,
}
