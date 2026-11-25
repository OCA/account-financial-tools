# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Account Account Control",
    "summary": """
        Control and audit the modifications of accounts used in posted
        journal entries""",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "maintainers": ["samirGuesmi"],
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Accounting",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_account.xml",
        "views/account_account_modification_reason.xml",
        "views/res_config_settings.xml",
        "wizards/account_account_modification_reason_wizard.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "account_account_control/static/src/js/*.esm.js",
        ],
    },
    "installable": True,
}
