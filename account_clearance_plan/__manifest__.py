# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Clearance Plan",
    "summary": """
        This addon allows to define clearance plans
        in order to reorganize debts (own and customers' ones).""",
    "version": "12.0.1.0.1",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": ["account"],
    "data": [
        "views/res_config_settings.xml",
        "wizard/account_clearance_plan_wizard.xml",
    ],
    "demo": [],
}
