# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2010 Zikzakmedia S.L. (http://www.zikzakmedia.com)
#    Copyright (c) 2010 Pexego Sistemas Informáticos S.L.(http://www.pexego.es)
#    Copyright (c) 2013 Joaquin Gutierrez (http://www.gutierrezweb.es)
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
#    $Id$
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
#    2013/09/08 - Joaquín Gutierrez: Adaptación a la versión
#
##############################################################################

{
    'name': "Detect changes and update the Account Chart from a template",
    'version': "1.2",
    'author': "Zikzakmedia SL",
    'website': "www.zikzakmedia.com",
    'depends': ["account"],
    'category': "Generic Modules/Accounting",
    'contributors': [
        'Joaquín Gutierrez',
        'Pedro M. Baeza',
        'invitu',
        'Stéphane Bidoul',
    ],
    'description': """
Adds a wizard to update a company account chart from a chart template.
======================================================================

This is a pretty useful tool to update OpenERP installations after tax reforms
on the official charts of accounts, or to apply fixes performed on the chart
template.

The wizard:

- Allows the user to compare a chart and a template showing differences
  on accounts, taxes, tax codes and fiscal positions.
- It may create the new account, taxes, tax codes and fiscal positions detected
  on the template.
- It can also update (overwrite) the accounts, taxes, tax codes and fiscal
  positions that got modified on the template.

The wizard lets the user select what kind of objects must be checked/updated,
and whether old records must be checked for changes and updates.
It will display all the accounts to be created / updated with some information
about the detected differences, and allow the user to exclude records
individually.

Any problem found while updating will be shown on the last step.
""",
    'license': "AGPL-3",
    "depends": [
        "account",
        "base",
    ],
    "demo": [],
    "data": [
        'wizard/wizard_chart_update_view.xml',
    ],
    "active": False,
    "installable": True
}
