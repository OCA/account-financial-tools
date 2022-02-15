# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Account Loan management",
    "version": "14.0.1.0.2",
    "author": "Creu Blanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "license": "AGPL-3",
    "category": "Accounting",
    "depends": ["account"],
    "data": [
        "data/ir_sequence_data.xml",
        "security/ir.model.access.csv",
        "security/account_loan_security.xml",
        "wizard/account_loan_generate_entries_view.xml",
        "wizard/account_loan_pay_amount_view.xml",
        "wizard/account_loan_post_view.xml",
        "views/account_loan_view.xml",
        "views/account_move_view.xml",
    ],
    "installable": True,
    "external_dependencies": {"python": ["numpy", "numpy-financial<=1.0.0"]},
}
