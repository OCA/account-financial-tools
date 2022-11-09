# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Move Total By Account Internal Group",
    "version": "15.0.1.0.0",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "summary": "Adds Totals by Account Internal Group in Journal Entries",
    "website": "https://github.com/OCA/account-financial-tools",
    "license": "AGPL-3",
    "depends": ["account"],
    "category": "Accounting",
    "data": [
        "views/account_move_views.xml",
    ],
    "installable": True,
    "maintainer": "AaronHForgeFlow",
    "development_status": "Beta",
    "pre_init_hook": "pre_init_hook",
}
