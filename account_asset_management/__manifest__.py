# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Assets Management',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'account_fiscal_year',
        'sale',
        'purchase',
        # 'account_recalculate_stock_move',
        'stock_picking_invoice_link',
        'stock_inventory_cost_info',
        'account_documents',
    ],
    'excludes': ['account_asset'],
    'author': "Rosen Vladimirov (Bioprint Ltd.), Noviat,Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/account-financial-tools',
    'category': 'Accounting & Finance',
    'data': [
        'security/account_asset_security.xml',
        'data/account_assets_actions.xml',
        'security/ir.model.access.csv',
        'wizard/account_asset_compute.xml',
        'wizard/account_asset_remove.xml',
        'wizard/account_invoice_asset.xml',
        'views/account_account.xml',
        'views/account_asset.xml',
        'views/product_template_view.xml',
        'views/product_view.xml',
        'views/account_asset_profile.xml',
        'views/account_asset_profile_bg.xml',
        'views/account_asset_category_view.xml',
        'views/res_config_settings.xml',
        'views/purchase_views.xml',
        'views/sale_views.xml',
        'views/account_invoice.xml',
        'views/account_invoice_line.xml',
        'views/account_move.xml',
        'views/account_move_line.xml',
        'views/account_asset_actions.xml',
        'views/stock_inventory_views.xml',
        'views/stock_picking_asset_lines.xml',
        'views/stock_picking_views.xml',
        'views/menuitem.xml',
    ],
}
