# -*- coding: utf-8 -*-
# Copyright 2014 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Automatic Fiscal Year Sequences',
    'version': '8.0.0.1.0',
    'category': 'Accounting',
    'author': "ACSONE SA/NV,Odoo Community Association (OCA)",
    'website': 'http://acsone.eu',
    'depends': ['account'],
    'data': [
        'views/ir_sequence_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
