# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2014 Therp BV (<http://therp.nl>).
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
    "name": "Move line search view - disable defaults for period and journal",
    "version": "8.0.0.1.0",
    "author": "Therp BV,Odoo Community Association (OCA)",
    "category": 'Accounting & Finance',
    'description': """
OpenERP 7.0 implements a custom javascript search view for move lines. This
search view shows dropdowns for period and journal. By default, these are
set to the default journal and (current) period.

This module leaves the search view extension for move lines intact, but
disables the default search values for the dropdowns so that you do not
have to disable these before entering your own search queries.
    """,
    'website': 'http://therp.nl',
    'license': 'AGPL-3',
    'depends': ['account'],
    'js': ['static/src/js/move_line_search_view.js'],
    'data': ['views/move_line_search_view.xml']
}
