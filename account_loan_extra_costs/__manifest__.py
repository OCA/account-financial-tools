# Copyright 2026 INVITU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Account Loan Extra Costs",
    "version": "18.0.1.0.0",
    "author": "INVITU, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "license": "AGPL-3",
    "category": "Accounting",
    "summary": "Manage insurance premiums, fees and other extra costs on loans",
    "depends": ["account_loan"],
    "data": [
        "security/ir.model.access.csv",
        "security/account_loan_extra_costs_security.xml",
        "views/account_loan_view.xml",
        "views/account_loan_line_view.xml",
    ],
    "demo": [
        "demo/loan_extra_cost_demo.xml",
    ],
    "installable": True,
    "maintainers": [],
}
