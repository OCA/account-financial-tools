# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011- Slobodni programi d.o.o.
#    @author: Goran Kliska
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
    "name": "Account storno",
    "description": """
 Enables Storno Accounting, a business practice commonly used in Eastern
 European countries.
 Adds new field "Posting policy" with values Storno/Contra on the Journal.
 For Storno Journals refund invoices are (usually) done in the same journal
 with negative *(-1) quantities.

Countries where Storno accounting is mandatory or considered as best practice:
     Czech Republic, Poland, Romania, Russia, China, Slovakia, Slovenia,
     Ukraine, Croatia, Bosnia and Herzegovina, Serbia, ...

WARNING:
 This module is managing accounting, invoices, and refund wizard.
 Other modules are required for stock, voucher, etc. storno posting.

Author: Goran Kliska @ Slobodni programi d.o.o.
        http://www.slobodni-programi.hr
Contributions:
  Ivan Vađić @ Slobodni programi d.o.o.
  Tomislav Bošnjaković @ Storm Computers d.o.o.: Bugs report

""",
    "version": "13.1",
    "author": "Slobodni programi d.o.o.",
    "category": "Localisation/Croatia",
    "website": "http://www.slobodni-programi.hr",
    'depends': ['account', 'account_voucher'],
    'init_xml': [],
    'update_xml': ['view/account_view.xml'],
    "demo_xml": [],
    'test': [],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
