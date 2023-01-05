# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Chatter on journal entries',
    'version': '12.0.1.0.0',
    'category': 'Invoices & Payments',
    'license': 'AGPL-3',
    'author': 'Tecnativa, '
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-tools',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_move_views.xml',
    ],
    'installable': True,
    'development_status': 'Beta',
    'maintainers': ['pedrobaeza'],
}
