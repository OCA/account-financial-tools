# Copyright 2023 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Move Line Attachment Preview",
    "summary": "Preview attachment on journal item list",
    "version": "16.0.1.0.0",
    "author": "Onestein,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Accounting/Accounting",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "depends": ["account", "attachment_preview"],
    "data": [
        "views/account_move_line.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "account_move_line_attachment_preview/static/src/**/*",
        ],
    },
}
