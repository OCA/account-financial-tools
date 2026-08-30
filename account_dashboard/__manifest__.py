# Copyright 2026 Heliconia Solutions Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


{
    "name": "Accounting Dashboard",
    "version": "18.0.1.0.0",
    "category": "Accounting & Finance",
    "summary": "Provides a custom accounting dashboard with quick reconciliation,"
    " balance details, and file uploads.",
    "author": "Odoo Community Association (OCA), Heliconia Solutions Pvt. Ltd.",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": [
        "account",
        "base",
        "account_reconcile_oca",
        "account_statement_import_file",
    ],
    "data": [
        "views/account_journal_view.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "AGPL-3",
    "development_status": "Beta",
    "maintainers": ["Bhavesh Heliconia"],
}
