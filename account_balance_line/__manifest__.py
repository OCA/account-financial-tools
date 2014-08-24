# -*- coding: utf-8 -*-
# Copyright 2010-2014 Camptocamp - Vincent Renaville
# Copyright 2016 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Balance on journal items',
    'summary': 'Display balance totals in move line view',
    'version': '10.0.1.0.0',
    'category': 'Accounting',
    'website': 'http://www.tecnativa.com,',
    'author': "Camptocamp,"
              "Tecnativa,"
              "Odoo Community Association (OCA)",
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'account'
    ],
    'data': [
        'views/account_move_line_view.xml'
    ],
}
