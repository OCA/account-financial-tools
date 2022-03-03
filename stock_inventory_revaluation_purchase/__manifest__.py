# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Stock Inventory Revaluation Purchase",
    "summary": "Stock Inventory Revaluation Purchase",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "ForgeFlow S.L., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": [
        "stock_inventory_revaluation",
        "account_move_line_stock_info",
        "account_move_line_purchase_info",
    ],
    "data": [
        "views/res_config_settings_views.xml",
        "views/stock_inventory_revaluation_views.xml",
    ],
    "development_status": "Alpha",
    "maintainer": "AaronHForgeFlow",
}
