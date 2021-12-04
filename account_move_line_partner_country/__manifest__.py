# Copyright 2021 CorporateHub (https://corporatehub.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Accounting: Account Move Line Partner's Country",
    "summary": "Show Partner's Country on Account Move Line.",
    "version": "12.0.1.0.0",
    "category": "Accounting",
    "website": "https://github.com/OCA/account-financial-tools",
    "author": "CorporateHub, Odoo Community Association (OCA)",
    "maintainers": ["alexey-pelykh"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account",
    ],
    "data": [
        "views/account_move_line.xml",
    ],
}
