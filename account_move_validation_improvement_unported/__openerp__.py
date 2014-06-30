# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville/Joel Grand-Guillaume. Copyright 2012 Camptocamp SA
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
##############################################################################
{
    "name" : "Wizard to validate multiple moves",
    "version" : "1.0",
    "depends" : ["base", "account", "account_constraints"],
    "author" : "Camptocamp",
    'license': 'AGPL-3',
    "description": """
Re-defining a base wizard (validate all moves in a period for a journal),
but extending it to multiple periods and multiple journals. It replaces the
base one defined in addons/account/wizard.
    """,
    'website': 'http://www.camptocamp.com',
    'data' : ['wizard/account_validate_move_view.xml'],
    'installable': False,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
