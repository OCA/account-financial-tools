# -*- coding: utf-8 -*-
# Copyright 2015-2017 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': "Account Move Template",
    'version': '8.0.1.0.0',
    'category': 'Generic Modules/Accounting',
    'summary': "Templates for recurring Journal Entries",
    'author': "Agile Business Group,Odoo Community Association (OCA), Aurium "
              "Technologies,Vauxoo",
    'website': 'http://www.agilebg.com , http://www.auriumtechnologies.com',
    'license': 'AGPL-3',
    'depends': ['account_accountant', 'analytic'],
    'data': [
        'security/ir.model.access.csv',
        'view/move_template.xml',
        'wizard/select_template.xml',
    ],
    'test': [
        'test/generate_move.yml',
    ],
    'active': False,
    'installable': True,
}
