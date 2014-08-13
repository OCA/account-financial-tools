# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
#    Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
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
    'name': "Account Move Template",
    'version': '0.1',
    'category': 'Generic Modules/Accounting',
    'summary': "Templates for recurring Journal Entries",
    'description': """
Templates for Journal Entries

User can configure journal entries templates, useful for recurring entries.
The amount of each template line can be computed (through python code) or kept as user input.
If user input, when using the template, user has to fill the amount of every input lines.
The journal entry form allows lo load, through a wizard, the template to use and the amounts to fill.

""",
    'author': 'Agile Business Group',
    'website': 'http://www.agilebg.com',
    'license': 'AGPL-3',
    'depends': ['account_accountant', 'analytic'],
    'data': [
        'move_template.xml',
        'wizard/select_template.xml',
        'security/ir.model.access.csv',
    ],
    'test': [
        'test/generate_move.yml',
    ],
    'active': False,
    'installable': False,
}
