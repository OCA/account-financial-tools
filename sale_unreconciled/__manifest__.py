# Copyright 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Sale Unreconciled",
    "version": "14.0.1.0.0",
    "author": "ForgeFlow S.L., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Accounting",
    "depends": ["sale_mrp", "account_move_line_sale_info"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order_view.xml",
        "views/res_config_settings_view.xml",
        "wizards/sale_unreconciled_exceeded_view.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["AaronHForgeFlow"],
}
