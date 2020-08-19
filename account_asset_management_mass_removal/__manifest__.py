# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Assets Management Mass Removal",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "summary": "Remove Mass Asset",
    "depends": ["mail", "account_asset_management"],
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Accounting & Finance",
    "data": [
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/account_asset_removal.xml",
        "views/menuitem.xml",
    ],
    "maintainers": ["Saran440"],
}
