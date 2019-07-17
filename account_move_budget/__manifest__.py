# Copyright 2019 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Move Budget",
    "summary": "Create Accounting Budgets",
    "version": "12.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/account-financial-tools",
    "author": "Eficent, "
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account",
        "date_range",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/account_move_budget_line_views.xml",
        "views/account_move_budget_views.xml",
    ],
}
