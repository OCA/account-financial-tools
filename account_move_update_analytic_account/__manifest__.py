# Copyright 2022 Le Filament
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account move update analytic account",
    "version": "14.0.1.0.0",
    "category": "Accounting & Finance",
    "summary": "This module allows the user to update analytic accounts on posted moves",
    "author": "Le Filament, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "license": "AGPL-3",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/account_move_update_analytic_view.xml",
        "views/account_move_view.xml",
        "views/account_move_line_view.xml",
    ],
    "installable": True,
}
