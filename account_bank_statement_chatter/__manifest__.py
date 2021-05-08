# Copyright 2021 Trey, Kilobytes de Soluciones - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Chatter on bank statements',
    'version': '12.0.1.0.0',
    'category': 'Invoices & Payments',
    'license': 'AGPL-3',
    'author': 'Trey, '
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-tools',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_bank_statement_views.xml',
    ],
    'installable': True,
    'development_status': 'Beta',
    'maintainers': ['cubells'],
}
