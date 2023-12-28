# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Asset Transfer from AUC to Asset",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["account_asset_management"],
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Accounting & Finance",
    "data": [
        "security/ir.model.access.csv",
        "views/account_asset.xml",
        "views/account_asset_profile.xml",
        "wizard/account_asset_transfer.xml",
    ],
    "maintainers": ["kittiu"],
}
