# Copyright (C) 2021 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Fiscal Years - Automatic Creation",
    "summary": "Automatically create new fiscal years, based on the datas"
    " of the last fiscal years",
    "version": "16.0.1.0.2",
    "category": "Accounting",
    "author": "GRAP,Odoo Community Association (OCA)",
    "maintainers": ["legalsylvain"],
    "website": "https://github.com/OCA/account-financial-tools",
    "license": "AGPL-3",
    "depends": [
        "account_fiscal_year",
    ],
    "data": [
        "data/ir_cron.xml",
    ],
}
