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
        "description": """
Pexego Account Adminitration Tools

Accounting wizards for administrators:

- Adds a wizard to import accounts from CSV files. This may be useful
    to import the initial accounts into OpenERP.

- Adds a wizard to import account moves from CSV files. This may be useful
    to import the initial balance into OpenERP.

- Adds a wizard to set the receivable/payable account of the partners,
    in moves and invoices where a generic receivable/payable account
    was used instead.

- Adds a wizard to revalidate confirmed account moves so their analytic
    lines are regenerated. This may be used to fix the data after bugs like
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
                        'account_importer_wizard.xml',
                        'account_move_importer_wizard.xml',
                        'move_partner_account_wizard.xml',
                        'revalidate_moves_wizard.xml',
            ],
        "installable": True,
        'active': False

}
 
