# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Re-booking The Manufacture production",
    "version": "11.0.21.0.0",
    "depends": [
        "account_recalculate_stock_move",
        "mrp",
        "mrp_bom_losses",
    ],
    'author': "Rosen Vladimirov, Bioprint Ltd.,",
    "website": 'https://github.com/rosenvladimirov/account-financial-tools',
    "category": "Finance",
    "data": [
        "data/account_recalculate_stock_move.xml",
        "wizard/rebuild_account_move.xml",
    ],
    'license': 'AGPL-3',
    "auto_install": False,
    'installable': True,
}
