# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville. Copyright 2012 Camptocamp SA
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
    "name": "Cancel invoice, check on bank statement",
    "version": "1.0",
    "depends": ["base",
                "account",
                "account_voucher",
                "account_cancel"],
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "description": """
Constraint forbidding to cancel an invoice already
imported in bank statement with a voucher.
    """,
    'website': 'http://www.camptocamp.com',
    'license': 'AGPL-3',
    'date': [],
    'installable': False,
    'active': False,
}
