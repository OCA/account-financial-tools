# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Account Move Line Valuation Restrict Price Change",
    "summary": """
        Allows to restrict account move line price changes if valuation is present""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": [
        "stock_account",
    ],
    "data": ["views/res_config_settings.xml"],
}
