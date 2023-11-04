# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Account Reversal Usability",
    "summary": """
        This module purpose is to improve the usability of the move line reverse functionality
        by adding:

            * a field that allows tagging a move line as needing to be reversed. The value of
              the field gets automatically set to False once a reversed entry is made.
            * a filter in the search view that allows selecting the moves that are flagged as
              needing to be reversed.
            * the reverse move in the form view""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": [
        "account",
    ],
    "data": [
        "views/account_move.xml",
    ],
    "demo": [],
}
