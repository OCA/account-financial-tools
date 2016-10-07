# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Account Fiscal Year',
    'version': '10.0.1.0.0',
    'category': 'Accounting',
    'author': 'Camptocamp SA,'
              'Odoo Community Association (OCA)',
    'website': 'http://www.camptocamp.com',
    'depends': [
        'account',
        'date_range'
    ],
    'data': [
        'data/date_range_type.xml',
        'views/date_range_type.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
