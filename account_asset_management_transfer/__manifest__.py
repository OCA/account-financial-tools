# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Assets Management Transfer",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["mail", "account_asset_management"],
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Accounting & Finance",
    "data": [
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/res_config_settings_views.xml",
        "views/account_asset_transfer.xml",
        "views/menuitem.xml",
    ],
    "maintainers": ["Saran440"],
}
