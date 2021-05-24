# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Disable Account Template Items",
    "version": "14.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "summary": "Allow to disable / enable account template items"
    " (tax, fiscal position, account)",
    "author": "GRAP, Odoo Community Association (OCA)",
    "maintainers": ["legalsylvain"],
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": [
        "account_menu",
    ],
    "data": [
        "views/view_account_account_template.xml",
        "views/view_account_fiscal_position_template.xml",
        "views/view_account_tax_template.xml",
    ],
    "installable": True,
}
