# Copyright 2026 ACSONE SA/NV (<http://acsone.eu>)
# @author Pierre Verkest <pierre@verkest.fr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Account Leasing",
    "version": "19.0.1.0.0",
    "author": "Pierre Verkest, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "license": "AGPL-3",
    "category": "Accounting",
    "depends": ["account", "account_loan"],
    "data": [
        "views/account_loan_lines_view.xml",
        "views/account_loan_view.xml",
        "wizards/account_loan_generate_entries_view.xml",
    ],
    "installable": True,
    "maintainers": ["etobella", "petrus-v"],
    "external_dependencies": {},
}
