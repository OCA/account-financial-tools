# -*- coding: utf-8 -*-
# © <2018> PRISEHUB CIA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Locking Dates for Journal Entry Posting',
    'version': '10.0.1.0.0',
    'category': '',
    'author': 'Cristian Salamea, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-tools',
    'license': 'AGPL-3',
    'data': [
        'views/account_view.xml'
    ],
    'depends': [
        'account_fiscal_year'
    ],
    'installable': True,
}
