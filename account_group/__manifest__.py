# coding: utf-8
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Groups for accounts",
    "summary": "Use v11 account groups feature",
    "version": "10.0.1.1.0",
    "category": "Accounting",
    "website": "https://github.com/OCA/account-financial-tools",
    "author": "Tecnativa,"
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/account_account_views.xml",
        "views/account_group_views.xml",
    ],
}
