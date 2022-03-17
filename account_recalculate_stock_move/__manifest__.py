# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Re-booking The Stock Move",
    "version": "11.0.2.1.0",
    "depends": [
        "account",
        "account_documents",
        "stock",
        "stock_account",
        "sale",
        "sale_stock",
        "purchase",
        "stock_landed_costs",
        "account_move_line_stock_info",
        "account_asset_management",
        "queue_job",
        "queue_job_batch",
    ],
    # "conflicts": [
    #     "purchase_stock_price_unit_sync",
    # ],
    'author': "Rosen Vladimirov, Bioprint Ltd.,",
    "website": 'https://github.com/rosenvladimirov/account-financial-tools',
    "category": "Finance",
    "data": [
        "data/account_recalculate_stock_move.xml",
        "views/stock_account_views.xml",
        "views/sale_views.xml",
        "views/purchase_views.xml",
        "views/account_invoice_view.xml",
        "views/product_views.xml",
        "views/stock_landed_cost_views.xml",
        "views/stock_scrap_views.xml",
        "views/account_move_line_view.xml",
        "wizard/create_transfer.xml",
        "wizard/revalidate_transfer.xml",
        "wizard/cancel_inventory.xml",
        "wizard/rebuild_account_move.xml",
        "wizard/rebuild_inventory_account_move.xml",
        "wizard/rebuild_invoice_account_move.xml",
        "wizard/rebuild_all_account_move.xml",
        "wizard/rebuild_moves_product.xml",
    ],
    'license': 'AGPL-3',
    "auto_install": False,
    'installable': True,
}
