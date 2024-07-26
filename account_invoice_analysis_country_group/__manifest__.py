# Copyright 2024 ForgeFlow SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Account Invoice Analysis Country Group",
    "summary": "Account Invoice Analysis Country Group",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Accounting",
    "version": "15.0.1.0.0",
    "depends": ["account"],
    "development_status": "Alpha",
    "data": [
        "views/account_invoice_report_views.xml",
    ],
    "installable": True,
    "pre_init_hook": "pre_init_hook",
}
