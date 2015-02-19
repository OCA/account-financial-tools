# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville/Joel Grand-Guillaume.
#    Copyright 2012 Camptocamp SA
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
    "name": "Move in draft state by default",
    "version": "1.0",
    "depends": ["base", "account", "account_constraints"],
    "author": "Camptocamp",
    'license': 'AGPL-3',
    "description": """
Let the generated move in draft on invoice and bank statement
validation. The main reason is to ease the user work day-to-day. At
first we used account_cancel, but this module allow to cancel posted
move and that's not allowed.

Two needs here:

- We want to be able to cancel an invoice (as soon as move are not
  validated) without making a refund. Posted move can't be canceled.
- We want to ensure all move generated from bank statement and invoice
  are generated in draft so we can still change them if needed.

Use this module with account_constraints (find it here:
https://launchpad.net/account-financial-tools or in
http://apps.openerp.com) and you'll get closely the same feature as
account_cancel, but with the insurance that user won't change posted
move.

The new framework will then be: always work with draft moves, allowing
people to change what they want. At the end of the period, validate all
moves. Till there, you ensure no-one can change something (or they'll
need to make a refund).

    """,
    'website': 'http://www.camptocamp.com',
    'data': ['account_view.xml',
             'invoice_view.xml',
             'res_config_view.xml',
             ],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
