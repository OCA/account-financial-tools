# -*- coding: utf-8 -*-
# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Blocked cost centers",
    "version": "8.0.1.0.0",
    "author": "Therp BV,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Accounting & Finance",
    "summary": "Allow to temporarily block cost centers",
    "depends": [
        'account_block_account',
        'account_cost_center',
    ],
    "data": [
        "views/account_cost_center.xml",
    ],
    "auto_install": True,
}
