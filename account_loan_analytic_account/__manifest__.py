# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Loan Analytic Account",
    "summary": """
        Add analytic distributions on account loan""",
    "version": "16.0.1.0.0",
    "website": "https://github.com/OCA/account-financial-tools",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "depends": ["account_loan", "analytic"],
    "data": [
        "views/account_loan.xml",
    ],
}
