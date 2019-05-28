# Copyright 2018 Oihane Crucelaegui - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Account Budget Template",
    "version": "11.0.1.2.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "author": "AvanzOSC,"
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": [
        "account_budget",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/crossovered_budget_template_view.xml",
        "views/crossovered_budget_view.xml",
        "views/res_config_settings_view.xml",
    ],
    "installable": True,
}
