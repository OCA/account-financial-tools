# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013-2015 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Journal Items Search Extension',
    'version': '0.3',
    'license': 'AGPL-3',
    'author': "Noviat,Odoo Community Association (OCA)",
    'category': 'Accounting & Finance',
    'description': """
Journal Items Search Extension
==============================

This module adds the 'Journal Items Search All' menu entry.

This menu entry adds a number of search fields on top of the List View rows.
These fields can be used in combination with the Search window.

The purpose of this view is to offer a fast drill down capability
when searching through large number of accounting entries.

The drill down is facilitated further by opening the Form View when clicking on
the sought-after entry.
This allows an intuitive click-through to the related accounting documents
such as the originating Bank Statement, Invoice, Asset, ...

    """,
    'depends': ['account'],
    'data': [
        'account_view.xml',
    ],
    'js': [
        'static/src/js/account_move_line_search_extension.js',
    ],
    'qweb': [
        'static/src/xml/account_move_line_search_extension.xml',
    ],
    'css': [
        'static/src/css/account_move_line_search_extension.css',
    ],
    'installable': True,
    'auto_install': False,
}
