# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2013 Camptocamp SA
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
{'name': 'Asynchronous move/move line CSV importer',
 'version': '0.1.2',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'maintainer': 'Camptocamp',
 'category': 'Accounting',
 'complexity': 'normal',
 'depends': ['base', 'account'],
 'description': """
This module allows you to import moves / move lines via CSV asynchronously.

You can access model in the journal entries menu -> Moves/ Move lines importer.
User must be an account manger.

To import a CSV simply save an UTF8 CSV file in the "file" field.
Then you can choose a CSV separator.

If volumetry is important you can tick "Fast import" check box.
When enabled import will be faster but it will not use orm and may
not support all CSV canvas.

- Entry posted option of journal will be skipped.
- AA lines will only be created when moves are posted.
- Tax lines computation will be skipped until the move are posted.

This option should be used with caution and preferably in conjunction with
provided canvas in tests/data

Then simply press import file button. The process will be run in background
and you will be able to continue your work.

When the import is finished you will received a notification and an
import report will be available on the record
""",
 'website': 'http://www.camptocamp.com',
 'data': ['data.xml',
          'view/move_line_importer_view.xml',
          'security/ir.model.access.csv',
          'security/multi_company.xml'],
 'demo': [],
 'test': [],
 'installable': False,
 'auto_install': False,
 'license': 'AGPL-3',
 'application': False,
 }
