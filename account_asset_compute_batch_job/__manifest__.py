# Copyright 2022 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Assets - Compute Depre. with Job Queue in Batch",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["account_asset_compute_batch", "queue_job"],
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Accounting & Finance",
    "data": [
        "security/ir.model.access.csv",
        "data/queue_data.xml",
        "views/account_asset_compute_batch.xml",
    ],
}
