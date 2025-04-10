# Copyright 2019-22 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Purchase Unreconciled",
    "version": "17.0.2.0.0",
    "author": "ForgeFlow S.L., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Purchases",
    "depends": ["account_move_line_purchase_info", "purchase_stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/purchase_order_view.xml",
        "views/res_config_settings_view.xml",
        "wizards/purchase_unreconciled_exceeded_view.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["AaronHForgeFlow"],
}
