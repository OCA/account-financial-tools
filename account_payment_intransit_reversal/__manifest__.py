# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    'name': 'Account Payment Intransit Reversal',
    'summary': 'Create reversed journal entries when cancel document',
    'version': '12.0.1.0.0',
    'author': 'Ecosoft,'
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-tools',
    'category': 'Accounting',
    'depends': [
        'account',
        'account_document_reversal',
        'account_payment_intransit',
    ],
    'data': [],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'development_status': 'alpha',
    'maintainers': ['Saran440'],
}
