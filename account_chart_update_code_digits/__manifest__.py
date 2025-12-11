# Copyright 2025 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

{
    "name": "Account Chart Update Code Digits",
    "summary": "Modify account chart digits lenght",
    "version": "18.0.1.0.1",
    "development_status": "Alpha",
    "category": "Accounting",
    "website": "https://github.com/OCA/account-financial-tools",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["EmilioPascual", "rafelbn"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account_chart_update",
    ],
    "data": [
        "wizards/wizard_chart_update_view.xml",
    ],
}
