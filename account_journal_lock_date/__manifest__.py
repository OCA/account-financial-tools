# Copyright 2017 ACSONE SA/NV
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Journal Lock Date',
    'summary': """Lock each journal independently""",
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV,Camptocamp,Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-tools',
    'data': [
        'views/account_move_view.xml',
        'views/account_journal_view.xml',
        'wizards/wizard_account_lock_journal_view.xml',
    ],
    'depends': ['account'],
    'instalable': True,
}
