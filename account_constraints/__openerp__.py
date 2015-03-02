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
    'name' : 'Account Constraints',
    'version' : '1.0',
    'depends' : [
                 'account',
                 'account_voucher',
                 'account_payment',
                 ],
    'author' : "Camptocamp,Odoo Community Association (OCA)",
    'category': 'Generic Modules/Accounting',
    'description': """
Add contraints in the accounting module of OpenERP to avoid bad usage by
users that lead to corrupted datas. This is based on our experience and
legal state of the art in other software.

Summary of constraints are:

* For legal reason (forbiden to modify journal entries which belongs to
  a closed fy or period) : Forbid to modify the code of an account if
  journal entries have been already posted on this account. This cannot be
  simply 'configurable' since it can lead to a lack of confidence in
  OpenERP and this is what we want to change.

* Forbid to change the type of account for 'consolidation' and 'view' if
  there are entries on it or its children.

* Add a constraint on reconcile object to forbid the reconciliation
  between different partners.

* Add a constraint on account move: you cannot pickup a date that is
  not in the fiscal year of the concerned period (this constraint is
  not in OpenERP 7.0).

* Forbid the user to delete any move linked to an invoice. Cancelling
  invoice still works, of course.

* Forbid the user to provide a secondary currency which is the same as
  the company currency (this constraint is not in OpenERP 7.0).

* Forbid to change the journal of a bank statement if you already have a
  line in it. This is done in the voucher, because this is the case that
  breaks: when a voucher is created and you change the journal, it results
  in having entries generated on various journal which is not consistent.

* Add contraint for Payment Order: if an invoice is imported in a
  payment order, forbid to reset the invoice to Cancel or Draft

* Forbid to remove the reconcile on opening entries. We introduce a new
  boolean field to distinguish the reconciliations made by the closing process
  from others.
  
* Remove the possibility to modify or delete a move line related to an
  invoice or a bank statement, no matter what the status of the move
  (draft, validated or posted). This is useful in a standard context but
  even more if you're using the account_default_draft_move module. This way you ensure
  that the user cannot make mistakes: even in draft State, he must pass through the 
  parent object to make his modification.

    """,
    'website': 'http://www.camptocamp.com',
    'init_xml': [],
    'update_xml': [],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
