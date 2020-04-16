# Copyright 2018-2020 PESOL (<https://www.pesol.es>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account Move Trigger',
    'version': '11.0.1.0.1',
    'license': 'AGPL-3',
    'author': "PESOL, Odoo Community Association (OCA)",
    'website': 'http://pesol.es',
    'category': 'Banking addons',
    'depends': ['account'],
    'data': ['security/ir.model.access.csv',
             'views/account_move_trigger.xml',
             'data/account_move_trigger_data.xml',
    ],
    'installable': True,
}
