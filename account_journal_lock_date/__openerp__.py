# -*- coding: utf-8 -*-
{
    'name': "Account Journal Lock Date",

    'summary': """
        Lock account journals independently""",

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
        'views/account_journal.xml',
    ],
}
