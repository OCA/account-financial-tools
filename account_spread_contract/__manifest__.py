# Copyright 2018-2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Cost-Revenue Spread Contract",
    "summary": "Spread costs and revenues from contracts",
    "version": "11.0.1.0.0",
    "development_status": "Beta",
    "author": "Onestein,Odoo Community Association (OCA)",
    "maintainers": ["astirpe"],
    "license": "AGPL-3",
    "website": "https://github.com/OCA/account-financial-tools/",
    "category": "Accounting & Finance",
    "depends": [
        "account_spread_cost_revenue",
        "contract",
    ],
    "data": [
        "views/account_analytic_account.xml",
        "views/account_spread_template.xml",
        "wizards/account_spread_contract_line_link_wizard.xml",
    ],
    "installable": True,
}
