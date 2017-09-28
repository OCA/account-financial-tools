# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Account Tag Category",
    "summary": "Group account tags by categories",
    "version": "10.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://www.camptocamp.com/",
    "author": "Camptocamp SA,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "account",
        "web_m2x_options"
    ],
    "data": [
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "wizard/update_tags.xml",
        "views/account.xml",
    ],
    "application": False,
    "installable": True,
}
