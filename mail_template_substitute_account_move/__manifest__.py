# Copyright 2024 Sodexis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Mail Template Substitute Account Move",
    "summary": "Module to support Mail Template Substitution for Account Move",
    "version": "17.0.1.0.0",
    "category": "Accounting",
    "website": "https://github.com/OCA/account-financial-tools",
    "author": "Sodexis, Odoo Community Association (OCA)",
    "maintainers": ["SodexisTeam"],
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "account",
        "mail_template_substitute",
    ],
    "auto_install": ["account", "mail_template_substitute"],
}
