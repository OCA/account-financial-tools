# -*- coding: utf-8 -*-
##############################################################################
#
#     This file is part of account_journal_entry_posted_async,
#     an Odoo module.
#
#     Copyright (c) 2015 ACSONE SA/NV (<http://acsone.eu>)
#
#     account_journal_entry_posted_async is free software:
#     you can redistribute it and/or modify it under the terms of the GNU
#     Affero General Public License as published by the Free Software
#     Foundation,either version 3 of the License, or (at your option) any
#     later version.
#
#     account_journal_entry_posted_async is distributed
#     in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
#     even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#     PURPOSE.  See the GNU Affero General Public License for more details.
#
#     You should have received a copy of the GNU Affero General Public License
#     along with account_journal_entry_posted_async.
#     If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "Account Journal Async Entry Posted",

    'summary': """
        Automatically post account journal entries asynchronously""",

    'description': """
This module add a new checkbox on the journal to post asynchronously entries
created for the journal without any manual validation.

In this module we take advantage of the queue and channel system from Odoo
Connector to sequentially post entries in background and therefore avoid
concurrent updates on ir_sequence when the system is intensely used.
    """,

    'author': "ACSONE SA/NV,Odoo Community Association (OCA)",
    'website': "http://acsone.eu",

    'category': 'Generic Modules/Accounting',
    'version': '0.1',
    'license': 'AGPL-3',

    'depends': [
        'account_move_batch_validate',
    ],
    'data': [
        'views/account_view.xml',
    ],
}
