# Copyright 2017 ACSONE SA/NV
# Copyright 2018 XOE Corp. SAS <https://xoe.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Journal Lock Date',
    'summary': """
        Lock each journal independently""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV,Odoo Community Association (OCA)',
    'website': 'https://acsone.eu/',
    'depends': ['account'],
    'data': [
        'views/account_journal.xml',
    ],
    'demo': [
    ],
}
