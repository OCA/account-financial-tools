# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Journal Lock To Date",
    "summary": "Lock each journal independently from a future date",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_journal.xml",
        "wizards/update_journal_lock_to_dates_views.xml",
    ],
    "installable": True,
}
