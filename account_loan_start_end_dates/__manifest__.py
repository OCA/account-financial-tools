# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Account Loan Start End Dates",
    "summary": """Add start and end dates on interest account lines in account loan""",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": ["account_loan", "account_invoice_start_end_dates"],
    "data": [
        "views/account_loan.xml",
    ],
    "demo": [],
}
