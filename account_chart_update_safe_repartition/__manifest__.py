# Copyright 2026 Binhex
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

{
    "name": "Account Chart Update Safe Repartition",
    "summary": "In-place tax repartition updates when moves are already posted",
    "version": "18.0.1.0.0",
    "category": "Accounting",
    "website": "https://github.com/OCA/account-financial-tools",
    "author": "Binhex, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["syci"],
    "depends": [
        "account_chart_update",
    ],
    "data": [
        "views/wizard_chart_update_view.xml",
    ],
}
