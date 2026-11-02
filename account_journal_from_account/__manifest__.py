# Copyright 2026 Heliconia Solutions Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


{
    "name": "Account Journal Creation from COA",
    "summary": "Create journals directly from chart of accounts",
    "version": "18.0.1.0.0",
    "category": "Accounting & Finance",
    "author": "Odoo Community Association (OCA), Heliconia Solutions Pvt. Ltd.",
    "website": "https://github.com/OCA/account-financial-tools",
    "license": "AGPL-3",
    "depends": [
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_action_data.xml",
        "views/account_account_views.xml",
        "views/res_config_settings_views.xml",
        "wizard/user_confirmation_wizard_view.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "development_status": "Beta",
    "maintainers": ["Bhavesh Heliconia"],
}
