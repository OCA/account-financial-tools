# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "No Default Account",
    "version": "14.0.1.0.0",
    "development_status": "Beta",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "maintainers": ["dreispt"],
    "summary": "Remove default expense account for vendor bills journal",
    "website": "https://github.com/OCA/account-financial-tools",
    "license": "AGPL-3",
    "depends": ["account"],
    "category": "Accounting/Accounting",
    "data": [
        "views/account_journal_views.xml",
    ],
    "installable": True,
}
