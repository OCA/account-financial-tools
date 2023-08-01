# Copyright 2016-2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Asset Batch Compute",
    "summary": """
        Add the possibility to compute assets in batch""",
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,ForgeFlow,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": ["account_asset_management", "queue_job"],
    "data": ["wizards/account_asset_compute_views.xml", "data/queue_data.xml"],
}
