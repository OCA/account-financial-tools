# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Account Loan management",
    "version": "17.0.1.0.0",
    "author": "Creu Blanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "license": "AGPL-3",
    "category": "Accounting",
    "depends": ["account"],
    "data": [
        "wizards/account_loan_increase_amount.xml",
        "data/ir_sequence_data.xml",
        "security/ir.model.access.csv",
        "security/account_loan_security.xml",
        "wizards/account_loan_generate_entries_view.xml",
        "wizards/account_loan_pay_amount_view.xml",
        "wizards/account_loan_post_view.xml",
        "views/account_loan_view.xml",
        "views/account_move_view.xml",
        "views/res_partner.xml",
        "views/account_loan_lines_view.xml",
    ],
    "installable": True,
    "maintainers": ["etobella"],
    "external_dependencies": {
        "python": ["numpy>=1.15", "numpy-financial<=1.0.0"],
        "deb": ["libatlas-base-dev"],
    },
}
