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

- Set the receivable/payable account of the partners, in moves and invoices
  where a generic receivable/payable account was used instead.

- Revalidate confirmed account moves so their analytic lines are regenerated.
  This may be used to fix the data after bugs like
  https://bugs.launchpad.net/openobject-addons/+bug/582988
  The wizard also lets you find account moves missing their analytic lines.

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
                        'move_partner_account.xml',
                        'revalidate_moves.xml',
                        'account_chart_checker.xml',
            ],
        "installable": True,
        'active': False

}
 
