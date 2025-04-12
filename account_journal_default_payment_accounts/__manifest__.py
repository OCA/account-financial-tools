# Copyright (C) 2025 - Today: Sylvain LE GAL (http://www.grap.coop)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Journal - Default Payment Accounts",
    "version": "16.0.1.0.4",
    "category": "Accounting",
    "license": "AGPL-3",
    "summary": "configure automatically outstanding and incoming" " payment accounts",
    "author": "GRAP, Odoo Community Association (OCA)",
    "maintainers": ["legalsylvain"],
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": ["account"],
    "data": ["views/view_account_journal.xml"],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
