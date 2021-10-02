# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Cost-Revenue Spread Extra Features",
    "summary": "Extra feature for account spread cost/revenue",
    "version": "14.0.1.0.0",
    "development_status": "Beta",
    "author": "Ecosoft,Odoo Community Association (OCA)",
    "maintainers": ["kittiu"],
    "license": "AGPL-3",
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Accounting & Finance",
    "depends": ["account_spread_cost_revenue"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/account_spread_link_move_line.xml",
        "views/account_spread.xml",
    ],
    "installable": True,
}
