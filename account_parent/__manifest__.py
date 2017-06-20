# -*- coding: utf-8 -*-
# Copyright (C) 2016 Steigend IT Solutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Parent Account',
    'summary': 'Restore account hierarchy and views',
    'author': 'Steigend IT Solutions, Odoo Community Association (OCA)',
    'website': 'http://www.steigendit.com',
    'category': 'Accounting',
    'version': '10.0.1.0.0',
    'depends': [
        'account'
    ],
    'data': [
        'data/account_type_data.xml',
        'views/account_view.xml',
        'views/open_chart.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
