# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    "name": "Account Sequence Option",
    "summary": "Manage sequence options for account.move, i.e., invoice, bill, entry",
    "version": "14.0.1.0.2",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "development_status": "Alpha",
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Accounting",
    "depends": ["account", "base_sequence_option"],
    "data": [
        "data/account_sequence_option.xml",
        "views/account_move_views.xml",
    ],
    "demo": ["demo/account_demo_options.xml"],
    "maintainers": ["kittiu"],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
}
