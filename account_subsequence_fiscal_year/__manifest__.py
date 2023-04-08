# Copyright (C) 2020 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Accounting Subsequences per Fiscal Years",
    "summary": "Allow to create sub sequences for account moves number, based"
    " on the fiscal years settings",
    "version": "12.0.1.0.0",
    "category": "Accounting",
    "author": "GRAP,Odoo Community Association (OCA)",
    "maintainers": ["legalsylvain"],
    "website": "https://github.com/OCA/account-financial-tools",
    "license": "AGPL-3",
    "depends": [
        "account",
    ],
    "data": [
        "views/view_res_config_settings.xml",
    ],
    "demo": [
        "demo/res_groups.xml",
    ],
    "images": [
        "static/description/res_config_setting.png",
    ],
}
