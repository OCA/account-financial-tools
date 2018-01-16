# -*- coding: utf-8 -*-
# Copyright 2014 Leonardo Pistone Camptocamp SA
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    'name': "Account Move Batch Validate",
    'version': '9.0.1.0.0',
    'author': "Camptocamp,Odoo Community Association (OCA)",
    'category': 'Finance',
    'complexity': 'normal',
    'depends': [
        'account_accountant',
        'connector',
    ],
    'website': 'https://github.com/OCA/account-financial-tools',
    'data': [
        'views/account_view.xml',
        'wizard/move_marker_view.xml',
    ],
    'license': 'AGPL-3',
}
