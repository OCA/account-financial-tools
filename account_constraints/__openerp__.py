# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Joel Grand-Guillaume. Copyright 2012 Camptocamp SA
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
    'name': 'Account Constraints',
    'version': '8.0.1.1.0',
    'depends': ['account'],
    'author': "Camptocamp,Odoo Community Association (OCA)",
    'license': 'AGPL-3',
    'category': 'Generic Modules/Accounting',
    'description': """
Account Constraints
===================

Add constraints in the accounting module of OpenERP to avoid bad usage
by users that lead to corrupted datas. This is based on our experiences
and legal state of the art in other software.

Summary of constraints are:

* Add a constraint on account move: you cannot pickup a date that is not
  in the fiscal year of the concerned period (configurable per journal)

* For manual entries when multicurrency:

  a. Validation on the use of the 'Currency' and 'Currency Amount'
     fields as it is possible to enter one without the other
  b. Validation to prevent a Credit amount with a positive
     'Currency Amount', or a Debit with a negative 'Currency Amount'

* Add a check on entries that user cannot provide a secondary currency
  if the same than the company one.

* Remove the possibility to modify or delete a move line related to an
  invoice or a bank statement, no matter what the status of the move
  (draft, validated or posted). This is useful in a standard context but
  even more if you're using `account_default_draft_move`. This way you ensure
  that the user cannot make mistakes even in draft state, he must pass through
  the parent object to make his modification.

  Contributors
  * Stéphane Bidoul <stephane.bidoul@acsone.eu>

    """,
    'website': 'http://www.camptocamp.com',
    'data': [
        'view/account_journal.xml',
        'view/account_bank_statement.xml',
    ],
    'installable': True,
}
