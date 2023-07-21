# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Account Document Reversal",
    "summary": "Create reversed journal entries when cancel document",
    "version": "13.0.1.0.4",
    "author": "Ecosoft,ForgeFlow,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Accounting & Finance",
    "depends": ["account", "sale", "purchase"],
    "data": [
        "wizard/reverse_account_document_wizard.xml",
        "views/account_view.xml",
        "views/account_move_view.xml",
        "views/account_payment_view.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "maintainers": ["kittiu"],
}
