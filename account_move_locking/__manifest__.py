# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Move locked to prevent modification",
    "version": "10.0.1.0.0",
    "depends": ["base", "account"],
    "author": "Camptocamp,Odoo Community Association (OCA)",
    'license': 'AGPL-3',
    'website': 'http://www.camptocamp.com',
    'data': ['views/account_view.xml',
             'wizard/account_lock_move_view.xml'],
    'installable': True,
}
