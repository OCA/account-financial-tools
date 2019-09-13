# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Find balance inconsistencies",
    "version": "10.0.1.0.0",
    "author": "Therp BV,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Accounting",
    "summary": "Helps finding the date a balance inconsistency was introduced",
    "depends": [
        'account',
    ],
    "data": [
        "wizards/account_find_balance_inconsistency.xml",
    ],
}
