# Copyright 2021 Opener B.V. <stefan@opener.amsterdam>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Journal Item Drilldown",
    "version": "12.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "summary": "Group journal items by the first 2 account group levels",
    "author": "Opener B.V., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": [
        "account",
    ],
    "data": [
        "views/account_move_line_view.xml",
    ],
    "post_init_hook": "post_init_hook",
    "pre_init_hook": "pre_init_hook",
    "installable": True,
}
