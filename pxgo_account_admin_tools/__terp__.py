# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Pexego Sistemas Informáticos. All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
        "name" : "Pexego - Account Admin Tools",
        "version" : "1.0",
        "author" : "Pexego",
        "website" : "http://www.pexego.es",
        "category" : "Enterprise Specific Modules",
        "description": """Account Tools for Administrators

Import tools:

- Import accounts from CSV files. This may be useful to import the initial
  accounts into OpenERP.

- Import account moves from CSV files. This may be useful to import the initial
  balance into OpenERP.


Check and Repair tools:

- Check the Chart of Accounts for problems in its structure. This will allow
  you to detect incoherences like the ones caused by bugs like
  https://bugs.launchpad.net/openobject-server/+bug/581137
  (the preordered tree [parent_left/parent_right] not matching the
  parent-child structure [parent_id]).

- Revalidate confirmed account moves so their analytic lines are regenerated.
  This may be used to fix the data after bugs like
  https://bugs.launchpad.net/openobject-addons/+bug/582988
  The wizard also lets you find account moves missing their analytic lines.

- Set the receivable/payable account of the partners, in moves and invoices
  where a generic receivable/payable account was used instead.

- Set the parent reference in account move lines where the receivable/payable
  account associated with the partner was used, but a partner reference wasn't
  set. This may fix cases where the receivable/payable amounts displayed in the
  partner form does not match the balance of the receivable/payable accounts.

- Set the reference in account moves, associated with invoices, that do not have
  the right reference (the reference from the invoice if it was a supplier
  invoice, or the number from the invoice if it was a customer invoice).
  This is useful to fix the account moves after changing the invoice references.
            """,
        "depends" : [
                        'base',
                        'account',
            ],
        "init_xml" : [],
        "demo_xml" : [],
        "update_xml" : [
                        'admin_tools_menu.xml',
                        'account_importer.xml',
                        'account_move_importer.xml',
                        'account_chart_checker.xml',
                        'revalidate_moves.xml',
                        'move_partner_account.xml',
                        'set_partner_in_moves.xml',
                        'set_invoice_ref_in_moves.xml',
            ],
        "installable": True,
        'active': False

}
 
