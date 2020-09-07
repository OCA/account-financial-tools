# Copyright 2016-2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Cost-Revenue Spread",
    "summary": "Spread costs and revenues over a custom period",
    "version": "13.0.1.0.0",
    "development_status": "Beta",
    "author": "Onestein,Odoo Community Association (OCA)",
    "maintainers": ["astirpe"],
    "license": "AGPL-3",
    "website": "https://github.com/OCA/account-financial-tools/",
    "category": "Accounting & Finance",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "security/account_spread_security.xml",
        "views/account_spread.xml",
        "views/account_move.xml",
        "views/res_company.xml",
        "views/account_spread_template.xml",
        "templates/assets.xml",
        "wizards/account_spread_invoice_line_link_wizard.xml",
        "data/spread_cron.xml",
    ],
    "installable": True,
}
