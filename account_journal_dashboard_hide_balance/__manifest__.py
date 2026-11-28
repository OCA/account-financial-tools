# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Journal Dashboard Hide Balance",
    "summary": "Hide bank and cash balances on the accounting dashboard "
    "until the user reveals them",
    "version": "18.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": ["account", "web_widget_masked_value"],
    "data": ["views/account_journal_dashboard.xml"],
    "assets": {
        "web.assets_backend": [
            "account_journal_dashboard_hide_balance/static/src/**/*",
        ],
        "web.assets_unit_tests": [
            "account_journal_dashboard_hide_balance/static/tests/**/*",
        ],
    },
    "installable": True,
}
