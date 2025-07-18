# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Dashboard Banner",
    "version": "18.0.1.1.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "summary": "Add a configurable banner on the accounting dashboard",
    "author": "Akretion,Odoo Community Association (OCA)",
    "maintainers": ["alexis-via"],
    "development_status": "Beta",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_journal_dashboard.xml",
        "views/account_dashboard_banner_cell.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "account_dashboard_banner/static/src/views/account_dashboard_kanban_banner.esm.js",
            "account_dashboard_banner/static/src/views/account_dashboard_kanban_banner.xml",
        ],
    },
    "post_init_hook": "create_default_account_dashboard_cells",
    "installable": True,
}
