# Copyright 2016-2020 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Costcenter",
    "summary": "Cost center information for invoice lines",
    "author": "Onestein, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Accounting",
    "version": "15.0.1.0.0",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "security/account_cost_center_security.xml",
        "views/account_cost_center_views.xml",
        "views/account_move_views.xml",
        "views/account_move_line_views.xml",
        "views/account_invoice_report_views.xml",
    ],
    "installable": True,
}
