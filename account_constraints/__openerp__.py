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
    'author' : 'Camptocamp',
    'category': 'Generic Modules/Accounting',
    'description': """
Add contraints in the accounting module of OpenERP to avoid bad usage by
users that lead to corrupted datas. This is based on our experiences and
legal state of the art in other software.

Summary of constraints are:

* For legal reason (forbiden to modify journal entries which belongs to
  a closed fy or period) : Forbid to modify the code of an account if
  journal entries have been already posted on this account. This cannot be
  simply 'configurable' since it can lead to a lack of confidence in
  OpenERP and this is what we want to change.

* Forbid to change type of account for 'consolidation' and 'view' if
  there is entries on it or his children.

* Add a constraints on reconcile object to forbid the reconciliation
  between different partner

* Add a constraint on account move: you cannot pickup a date that is not
  in the fiscal year of the concerned period (Not in 7.0)

* Forbid the user to delete any move linked to an invoice. Cancelling
  invoice still work obviously

* Add a check on entries that user cannot provide a secondary currency
  if the same than the company one. (Not in 7.0)

* Forbid to change the journal of a bank statement if you already have a
  line in it. This is done in the voucher, cause this is the case that
  break : when voucher is created and you change the journal, it'll result
  in having entries generated on various journal which is not consistent.

* Add contraint for Payment Order : If a invoice is imported in a
  payment order, forbid to reset invoice to cancel or draft

* Forbid to remove the reconcile on opening entries, we introduce a new
  boolean field to identify the reconciliation made by the closing process
  from others.
    """,
    'website': 'http://www.camptocamp.com',
    'init_xml': [],
    'update_xml': [],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
