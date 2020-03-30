# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    'name': 'Account Payment Intransit',
    'version': '12.0.1.0.0',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'summary': 'Manage process the payment in-transit',
    'description': 'This module based on account_check_deposit',
    'author': 'Ecosoft, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-tools',
    'depends': [
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/payment_intransit_security.xml',
        'data/sequence.xml',
        'views/account_payment_intransit_view.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'maintainers': ['Saran440'],
}
