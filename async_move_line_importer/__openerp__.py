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
{'name': 'Asynchron move line importer',
 'version': '0.1.1',
 'author': 'Camptocamp',
 'maintainer': 'Camptocamp',
 'category': 'categ',
 'complexity': 'normal',
 'depends': ['base', 'account'],
 'description': """Allows to move/moveline asynchronously""",
 'website': 'http://www.camptocamp.com',
 'data': ['data.xml',
          'view/move_line_importer_view.xml',
          'security/ir.model.access.csv',
          'security/multi_company.xml'],
 'demo': [],
 'test': [],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 'application': False,
 }
