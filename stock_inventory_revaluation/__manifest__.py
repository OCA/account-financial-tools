# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Stock Inventory Revaluation",
    "summary": "Stock Inventory Revaluation",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "ForgeFlow S.L., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": ["stock_account"],
    "data": [
        "security/ir.model.access.csv",
        "data/stock_inventory_revaluation_data.xml",
        "views/account_move_views.xml",
        "views/stock_valuation_layer_views.xml",
        "views/stock_inventory_revaluation_views.xml",
    ],
    "development_status": "Alpha",
    "maintainer": "AaronHForgeFlow",
}
