# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Accounting - Multi branch company",
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    "category": "Accounting",
    "summary": "Add branch on Invoices/Bills",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": ["account", "base_multi_branch_company"],
    "data": [
        "views/account_move_view.xml",
        "views/account_payment_view.xml",
    ],
    "installable": True,
    "maintainers": ["Saran440"],
}
