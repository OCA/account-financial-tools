# -*- coding: utf-8 -*-
# Copyright 2018 PlanetaTIC - Lluís Rovira <lrovira@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Outstanding balance on journal items',
    'summary': 'Display outstanding balance in move line view',
    'version': '10.0.1.0.0',
    'category': 'Accounting',
    'author': 'PlanetaTIC',
    'website': 'https://www.planetatic.com',
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
