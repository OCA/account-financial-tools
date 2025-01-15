# Copyright 2019 ForgeFlow S.L.
# Copyright 2023 Simone Rubino - Aion Tech
# Copyright 2025 Innovyou
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Lock To Date",
    "summary": """
        Allows to set an account lock date in the future.""",
    "version": "16.0.2.0.0",
    "license": "AGPL-3",
    "author": "ForgeFlow, Innovyou, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "installable": True,
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/account_update_lock_to_date.xml",
        "data/cron.xml",
    ],
}
