# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Clearance Plan Bank Payment",
    "summary": """Support banking payment for clearance plan.""",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": [
        "account_banking_mandate",
        "account_clearance_plan",
        "account_payment_mode",
    ],
    "data": ["wizard/account_clearance_plan_wizard.xml"],
    "demo": [],
}
