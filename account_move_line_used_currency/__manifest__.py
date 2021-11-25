# Copyright 2021 ForgeFlow, S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Account Move Line Amount Currency",
    "version": "13.0.1.0.0",
    "website": "https://github.com/OCA/account-financial-tools",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "category": "Accounts",
    "license": "LGPL-3",
    "depends": ["account"],
    "data": ["views/account_move_line_view.xml", "views/account_move_view.xml"],
    "pre_init_hook": "pre_init_hook",
    "installable": True,
}
