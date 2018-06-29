# -*- coding: utf-8 -*-
# Author: Vincent Renaville
# Copyright 2013 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Tax analysis",
    "version": "10.0.1.0.0",
    "description": """
        Add a report on tax (Invoicing / Reports / Taxes Analysis)""",
    "depends": [
        "base",
        "account",
    ],
    "author": "Camptocamp SA, ACSONE SA/NV, Odoo Community Association (OCA)",
    "category": 'Accounting & Finance',
    "website": "http://www.camptocamp.com",
    "license": "AGPL-3",
    "data": [
        "wizard/account_tax_analysis_view.xml",
        "views/account_move_line.xml",
    ],
    "installable": True,
}
