# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Account Deactivation Date",
    "summary": "Deactivate accounts from a given date, keeping entries dated "
    "before it valid",
    "version": "18.0.1.0.0",
    "category": "Accounting/Accounting",
    "license": "AGPL-3",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "maintainers": ["marcelsavegnago"],
    "development_status": "Beta",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": [
        "account",
    ],
    "data": [
        "data/ir_cron.xml",
        "views/account_account_views.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
}
