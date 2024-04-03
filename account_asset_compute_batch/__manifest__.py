# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Assets - Compute Depre. in Batch",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["account_asset_management"],
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Accounting & Finance",
    "data": [
        "data/service_cron.xml",
        "security/account_asset_security.xml",
        "security/ir.model.access.csv",
        "wizard/account_asset_compute.xml",
        "views/account_asset_compute_batch.xml",
    ],
}
