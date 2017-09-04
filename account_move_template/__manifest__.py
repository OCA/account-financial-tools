# -*- coding: utf-8 -*-
# Copyright 2015-2017 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': "Account Move Template",
    'version': '10.0.2.0.0',
    'category': 'Generic Modules/Accounting',
    'summary': "Templates for recurring Journal Entries",
    'author': "Agile Business Group,Odoo Community Association (OCA), Aurium "
              "Technologies,Vauxoo",
    'website': 'https://github.com/OCA/account-financial-tools',
    'license': 'AGPL-3',
    'depends': ['account_accountant', 'analytic'],
    'data': [
        'security/ir.model.access.csv',
        'view/move_template.xml',
        'wizard/select_template.xml',
    ],
    'test': [
    ],
    'installable': True,
}
