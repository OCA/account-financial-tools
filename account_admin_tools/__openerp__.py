# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Pexego Sistemas Informáticos. All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
    "name": "Account Admin Tools",
    "version": "6.1",
    "author": "Pexego",
    "website": "http://www.pexego.es",
    "category": "Enterprise Specific Modules",
    "description": """Account Tools for Administrators
Check and Repair tools:

- Set the receivable/payable account of the partners, in moves and invoices
  where a generic receivable/payable account was used instead.

- Set the parent reference in account move lines where the receivable/payable
  account associated with the partner was used, but a partner reference wasn't
  set. This may fix cases where the receivable/payable amounts displayed in the
  partner form does not match the balance of the receivable/payable accounts.

- Set the reference in account moves, associated with invoices, that do not
  have the right reference for supplier invoices.
  This is useful to fix the account moves after changing the invoice
  references.
            """,
    "depends": [
    'base',
    'account',
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
    'admin_tools_menu.xml',
    'move_partner_account.xml',
    'set_partner_in_moves.xml',
    'set_invoice_ref_in_moves.xml',
    ],
    "installable": True,
    'active': False

}
