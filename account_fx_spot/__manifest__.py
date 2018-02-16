# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Account Forex Spot",
    "version": "11.0.1.0.0",
    "summary": "Adds support for  Foreign Exchange Spot Transactions.",
    "author": "Eficent, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Accounting",
    "depends": ["account"],
    "data": [
        "data/account_fx_spot_data.xml",
        "security/ir.model.access.csv",
        "views/account_fx_spot_payment.xml",
        "views/account_fx_view.xml",
        "views/account_payment.xml",
    ],
    "auto_install": False,
    "installable": True,
}
