# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Account Move Line Balance Update",
    "summary": "Update a journal item balance together with its counterpart",
    "version": "17.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/account-financial-tools",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["carlosdauden"],
    "license": "AGPL-3",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/account_move_line_balance_update_wizard.xml",
        "views/account_move_line_views.xml",
    ],
    "installable": True,
}
