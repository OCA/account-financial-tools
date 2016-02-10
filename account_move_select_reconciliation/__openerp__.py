# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Agile Business Group sagl
#    (<http://www.agilebg.com>)
#    @authors Alex Comba <alex.comba@agilebg.com>
#             Lorenzo Battistini <lorenzo.battistini@agilebg.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
    'name': "Account Move Select Reconciliation",
    'version': '0.1',
    'category': 'Finance',
    'description': """
This module allows to manually select the journal item to be reconciled while
registering a journal entry.

**Example** (also see the included test case)

You have an open credit and you need to close it by a manual journal entry.
With this module you can manually create the payment journal entry, select the
open credit and click 'Reconcile Line'. The system will close the credit
generating the respective reconciliation.
    """,
    'author': 'Agile Business Group',
    'website': 'http://www.agilebg.com',
    'license': 'AGPL-3',
    "depends": [
        'account_accountant',
    ],
    "data": [
        'account_move_view.xml',
    ],
    "test": [
        'test/account.yml',
        ],
    "active": False,
    "installable": True
}
