# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 Bringsvor Consulting AS. All rights reserved.
#    @author Torvald B. Bringsvor
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
    'name': 'Enforce tax account',
    'category': 'Accounting',
    'summary': 'Enforce tax Account',
    'version': '1.0',
    'description': """Forces movelines for a given account to have a given tax code.
    It is quite common in other systems to have the possibility to control VAT by
    bookkeeping accounts.
    """,
    'author': 'Bringsvor Consulting AS',
    'website': 'http://www.bringsvor.com',
    'depends': ['base', 'account'],
    'data': [
        'views/account_move_view.xml',
    ],
    'test': [
        ],
    'installable': True,
}
