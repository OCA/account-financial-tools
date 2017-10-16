# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Journal Items Search Extension',
    'version': '8.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Noviat, Odoo Community Association (OCA)',
    'category': 'Accounting & Finance',
    'depends': ['account'],
    'data': [
        'views/account_move_line.xml',
        'views/account_assets_backend.xml',
    ],
    'qweb': [
        'static/src/xml/account_move_line_search_extension.xml',
    ],
    'installable': True,
}
