# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Agile Business Group sagl
#    (<http://www.agilebg.com>)
#    @authors Lorenzo Battistini <lorenzo.battistini@agilebg.com>
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
    "name": "Reopen reconciliation",
    "version": "0.1",
    'category': 'Generic Modules/Accounting',
    "depends": ["account"],
    "author": "Agile Business Group",
    "description": """
This module allows to reopen reconciliations by creating an additional journal
entry and unreconciling the existing journal items.

See the following example

**Confirmed invoice**

==== ========= ====== ======
 N    Account   DR     CR
==== ========= ====== ======
 1A   Debtors   1000
 1B   Sales            1000
==== ========= ====== ======

**Paid invoice**

==== ========= ====== ======
 N    Account   DR     CR
==== ========= ====== ======
 2A   Bank      1000
 2B   Debtors          1000
==== ========= ====== ======

*1A* and *2B* are reconciled by *A1*

**Reopening**

For example, the bank takes back the money. You have to reopen the credit.

So, you can select the *1A* journal item and run the *reopen reconciliation*
wizard.

The module generates the following entry

==== ========= ====== ======
 N    Account   DR     CR
==== ========= ====== ======
 3A   Debtors   1000
 3B   Bank             1000
==== ========= ====== ======

The module cancels the *A1* reconciliation and create a new one between
*2B* and *3A*

""",
    'website': 'http://www.agilebg.com',
    'data': [
        'account_move_view.xml',
        'account_move_line_view.xml',
        'wizard/account_reopen_reconciliation_view.xml',
        ],
    'demo': [
        ],
    'test': [
        'test/account.yml',
        ],
    'installable': True,
    'active': False,
}
