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
{'name': 'Payment Order Extension',
 'summary': 'Add an improved view for payment order',
 'version': '1.1',
 'author': 'Camptocamp',
 'maintainter': 'Camptocamp',
 'category': 'Accounting',
 'depends': ['account_payment'],
 'description': """
Payment Order
==================

Add improved move line selection for multi-currency

Contributors
------------

* Vincent revaville <vincent.renaville@camptocamp.com>
""",
 'website': 'http://www.camptocamp.com',
 'data': ['payment_view.xml'],
 'tests': [],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 'application': False,
 }
