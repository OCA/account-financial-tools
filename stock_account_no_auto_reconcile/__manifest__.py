# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Stock Account No Auto Reconcile",
    "summary": "Do not try to reconcile stock interim related JE",
    "version": "15.0.1.0.0",
    "category": "Accounting",
    "author": "Odoo Community Association (OCA), ForgeFlow, ",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": ["purchase_stock", "sale_stock"],
    "data": ["views/res_config_settings_views.xml"],
}
