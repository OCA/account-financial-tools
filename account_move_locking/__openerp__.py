# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville.
#    Copyright 2015 Camptocamp SA
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
    "name": "Move locked to prevent modification",
    "version": "8.0.1.0.0",
    "depends": ["base", "account"],
    "author": "Camptocamp,Odoo Community Association (OCA)",
    'license': 'AGPL-3',
    'website': 'http://www.camptocamp.com',
    'data': ['account_view.xml',
             'wizard/account_lock_move_view.xml'],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
