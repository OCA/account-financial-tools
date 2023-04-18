# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Move Fiscal Year',
    'summary': """
        Display the fiscal year on journal entries/item""",
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-tools',
    'depends': [
        'account_fiscal_year',
    ],
    'data': [
        'views/account_move.xml',
        'views/account_move_line.xml',
    ],
}
