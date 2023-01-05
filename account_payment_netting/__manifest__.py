# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    'name': 'Account Payment Netting',
    'version': '12.0.1.0.1',
    'summary': 'Net Payment on AR/AP invoice from the same partner',
    'category': 'Accounting & Finance',
    'author': 'Ecosoft, '
              'Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'website': 'https://github.com/OCA/account-financial-tools',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_invoice_view.xml',
        'views/account_payment_view.xml',
    ],
    'installable': True,
    'development_status': 'Beta',
    'maintainers': ['kittiu'],
}
