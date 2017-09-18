# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville. Copyright 2012 Camptocamp SA
#    Fabien Moret. Copyright 2017 Martronic SA
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
    "name": "Cancel invoice, check on payment order",
    "version": "9.0.1.0.1",
    "depends": ["account",
                "account_payment_order",
                "account_cancel"],
    "author": "Camptocamp,Martronic SA,Odoo Community Association (OCA)",
    "description": """
Prevents to cancel an invoice which has already been imported in a
payment order.
    """,
    'website': 'http://www.camptocamp.com',
    'license': 'AGPL-3',
    'data': [],
    'installable': True,
    'active': True,
}
