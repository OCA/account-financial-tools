# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Move Line Tax Editable',
    'summary': """
        Allows to edit taxes on non-posted account move lines""",
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV,Odoo Community Association (OCA)',
    'website': 'https://www.acsone.eu',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_move.xml',
        'views/account_move_line.xml',
    ],
}
