# -*- coding: utf-8 -*-
# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Blocked accounts",
    "version": "8.0.1.0.0",
    "author": "Therp BV,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Accounting & Finance",
    "summary": "Allow to temporarily block accounts",
    "depends": [
        'account',
    ],
    "data": [
        "views/account_analytic_account.xml",
        "views/account_account.xml",
    ],
}
