# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Account Move Restricted by Account Groups",
    "summary": "Restrict visibility of journal entries by security groups on accounts.",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "author": "Quartile, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "license": "AGPL-3",
    "depends": ["account"],
    "data": [
        "security/account_move_group_restriction_security.xml",
        "views/account_account_view.xml",
    ],
    "maintainers": ["kanda999", "aungkokolin1997"],
    "installable": True,
    "application": False,
}
