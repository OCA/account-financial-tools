# -*- coding: utf-8 -*-
{
    'name': "Account Journal Lock Date",

    'summary': """
        Lock account journals independently""",

    'description': """
        Lock account journals independently.
        This is a backport of version 10.0 module of the same name by Stéphane Bidoul.

        https://github.com/OCA/account-financial-tools/tree/10.0/account_journal_lock_date
    """,

    'author': "Coop IT Easy SCRL",
    'website': "http://www.coopiteasy.be",

    'category': 'Accounting & Finance',
    'version': '9.0.1.0.0',

    'depends': [
        'base',
        'account',
        'account_permanent_lock_move',
    ],

    'data': [
        'views/journal_lock_views.xml',
    ],
}
