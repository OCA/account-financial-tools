# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Account Move Reverse Reconcile",
    "summary": "Define if reversal moves have to be reconciled",
    "version": "18.0.1.0.0",
    "development_status": "Alpha",
    "category": "Accounting",
    "website": "https://github.com/OCA/account-financial-tools",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["grindtildeath"],
    "license": "AGPL-3",
    "installable": True,
    "pre_init_hook": "pre_init_hook",
    "depends": [
        "account",
    ],
    "data": [
        "views/account_journal.xml",
        "views/account_move.xml",
    ],
}
