# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2014 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Void Voucher Reverse Entries',
    'version': '0.1',
    'author': 'Savoir-faire Linux',
    'maintainer': 'Savoir-faire Linux',
    'website': 'http://www.savoirfairelinux.com',
    'license': 'AGPL-3',
    'category': 'Accounting',
    'summary': 'Voiding a voucher will create reversal entries',
    'description': """
Void a voucher will create reversal entries
===========================================

By default, you can cancel a voucher by clicking the 'Unreconcile' button.
This action will unreconcile the paid invoice and set the voucher to 'Cancel' state.
This is not always a good way to operate for many reasons :

* the period is closed;
* tax reports have already been issued;
* you want to keep the history of the vouchers.

This module does the following :

* add a "Void check" button;
* clicking the 'Void' button will create reversal entries;
* all the entries are prefixed with the string 'REV -'
* add a new end state 'Void' to the account_voucher model

Contributors
------------
* Vincent Vinet (vincent.vinet@savoirfairelinux.com)
* Marc Cassuto (marc.cassuto@savoirfairelinux.com)
""",
    'depends': [
        'account_check_writing',
        'account_reversal',
        'account_voucher',
    ],
    'external_dependencies': {
        'python': [],
    },
    'data': [
        'account_voucher_view.xml'
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
