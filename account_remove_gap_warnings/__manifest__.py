# Copyright 2024 Miika Nissi (https://miikanissi.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Accounting: Remove Gap Warnings",
    "version": "16.0.1.0.0",
    "category": "Hidden",
    "website": "https://github.com/OCA/account-financial-tools",
    "author": "Geschäftsstelle Sozialinfo, Miika Nissi, Odoo Community Association (OCA)",
    "maintainers": ["miikanissi"],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "depends": ["account"],
    "data": ["views/account_journal_dashboard_view.xml"],
    "assets": {
        "web.assets_backend": [
            (
                "after",
                "account/static/src/components/account_move_service/account_move_service.js",
                "account_remove_gap_warnings/static/src/js/account_move_service.esm.js",
            ),
        ],
    },
}
