# Copyright 2020 Lorenzo Battistini @ TAKOBI
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Account journals - Restrict users",
    "summary": "Restrict some users to see and use only certain journals",
    "version": "12.0.1.0.0",
    "development_status": "Beta",
    "category": "Invoicing Management",
    "website": "https://github.com/OCA/account-financial-tools",
    "author": "TAKOBI, Odoo Community Association (OCA)",
    "maintainers": ["eLBati"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account",
    ],
    "data": [
        "security/account_security.xml",
        "views/account_journal_views.xml",
        "security/ir.model.access.csv",
        "views/account_report.xml",
        "views/account_invoice_view.xml",
    ],
}
