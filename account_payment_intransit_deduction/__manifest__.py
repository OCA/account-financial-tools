# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    'name': 'Payment Intransit with Multiple Deduction',
    'version': '12.0.1.0.0',
    'author': 'Ecosoft, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'website': 'https://github.com/OCA/account-payment/',
    'category': 'Accounting',
    'depends': [
        'account_payment_intransit',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_payment_intransit_view.xml'
    ],
    'installable': True,
    'development_status': 'alpha',
    'maintainers': ['Saran440'],
}
