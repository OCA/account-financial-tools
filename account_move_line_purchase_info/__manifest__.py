# -*- coding: utf-8 -*-
# Copyright 2020 ForgeFlow, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Move Line Purchase Info",
    "summary": "Introduces the purchase order line to the journal items",
    "version": "10.0.1.0.0",
    "author": "ForgeFlow, "
              "Odoo Community Association (OCA)",
    "website": "http://www.github.com/OCA/account-financial-tools",
    "category": "Generic",
    "depends": ["account_accountant", "purchase"],
    "license": "AGPL-3",
    "data": [
        "security/account_security.xml",
        "views/account_move_view.xml",
    ],
    'installable': True,
}
