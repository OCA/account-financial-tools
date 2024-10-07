# Copyright 2024 ACSONE SA/NV
# Copyright 2024 ADHOC SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Account Move Show Draft Button",
    "summary": """
        This module allows to reset an account move to draft even if there are valuation
          lines""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,ADHOC SA,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": ["stock_account"],
    "data": [
        "security/security.xml",
        "views/account_move.xml",
    ],
}
