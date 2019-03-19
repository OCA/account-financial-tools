# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    'name': 'Base Account Reversal',
    'summary': 'Base module for create reversal journal entries',
    'version': '12.0.1.0.0',
    'author': 'Ecosoft,Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-tools',
    'category': 'Accounting & Finance',
    'depends': ['account_cancel'],
    'data': [
        'wizard/reverse_account_document_wizard.xml',
        'views/account_view.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
}
