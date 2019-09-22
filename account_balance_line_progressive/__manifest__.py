# Copyright 2016-2019 Sergio Corato <https://github.com/sergiocorato>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{
    'name': 'Account balance line progressive',
    'version': '12.0.1.0.0',
    'category': 'Accounting',
    'description': 'View balance in account line tree. '
    'Instead of module account_balance_line, wich show the balance only of the'
    ' single line, it compute progressive balance for the account selected.',
    'author': "Sergio Corato, "
              "Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/account-financial-tools',
    'license': 'LGPL-3',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_move_line.xml',
    ],
    'installable': True,
}
