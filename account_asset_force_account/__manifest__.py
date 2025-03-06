# Copyright 2024 Bernat Obrador(APSL-Nagarro)<bobrador@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Asset Force Account",
    "summary": "This module allows you to enforce specific accounts for assets, including depreciation and expense accounts, through asset profiles and forms.",
    "version": "17.0.1.1.0",
    "website": "https://github.com/OCA/account-financial-tools",
    "author": "Bernat Obrador (APSL-Nagarro), Odoo Community Association (OCA)",
    "category": "Accounting & Finance",
    "maintainers": ["BernatObrador"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account_asset_management",
    ],
    "data": [
        "views/account_asset.xml",
    ],
}
