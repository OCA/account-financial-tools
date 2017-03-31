# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': "Account Move Line Payable Receivable Filter",

    'summary': """
        Filter your Journal Items per payable and receivable account""",
    'author': "ACSONE SA/NV,Odoo Community Association (OCA)",
    'website': "http://acsone.eu",
    'category': 'Accounting & Finance',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_move_line_view.xml',
    ],
    'installable': True,
}
