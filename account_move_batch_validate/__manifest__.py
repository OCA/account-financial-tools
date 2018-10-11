# Copyright 2014 Camptocamp SA, 2017 ACSONE
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': "Account Move Batch Validate",
    'version': '11.0.1.0.0',
    'author': "Camptocamp, Odoo Community Association (OCA)",
    'website': 'http://www.camptocamp.com',
    'category': 'Finance',
    'complexity': 'normal',
    'depends': [
        'account',
        'queue_job',
    ],
    'data': [
        'views/account_move.xml',
        'wizard/account_move_validate.xml',
    ],
    'installable': True,
    'license': 'AGPL-3',
}
