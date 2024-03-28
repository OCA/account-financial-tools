# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Journal Lock Date",
    "summary": "Lock each journal independently",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV, Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_journal.xml",
        "wizards/update_journal_lock_dates_views.xml",
    ],
    "demo": [],
    "installable": True,
}
