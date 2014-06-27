# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Vincent Renaville (Camptocamp)
#    Copyright 2010-2014 Camptocamp SA
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
{'name': 'Balance on lines',
 'summary': 'Display balance totals in move line view',
 'version': '8.0.1.1.0',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'maintainter': 'Camptocamp',
 'category': 'Accounting',
 'depends': ['account'],
 'description': """
Balance for a line
==================

Add a balance total for grouped lines in move line view.

Balance field will only be shown when move lines are grouped by account
or filtered by account.

Contributors
------------

* Vincent revaville <vincent.renaville@camptocamp.com>
* Yannick Vaucher <yannick.vaucher@camptocamp.com>
""",
 'website': 'http://www.camptocamp.com',
 'data': ['account_move_line_view.xml'],
 'tests': [],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 'application': False,
 }
