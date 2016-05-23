# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Therp BV (<http://therp.nl>).
#    Copyright (C) 2013 Camptocamp SA.
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
    "name": "Update tax wizard",
    "version": "8.0.1.0.45",
    "author": "Therp BV, Camptocamp SA,Odoo Community Association (OCA)",
    "category": 'Base',
    'complexity': "normal",
    "description": """
This module aims at assisting the finance manager with implementing a tax
increase. Currently, only taxes that apply a percentage are covered.

The module creates a new menu item 'Update tax wizard' in the financial
settings menu, under the Taxes submenu. Using the wizard, you can select
the sales and purchase taxes that need to be upgraded and assign a new
percentage.

The selected taxes are in fact duplicated by running the wizard, so that
existing entries in the system are not affected. The new taxes are mapped
automatically in the appropriate fiscal positions. The wizard can replace
default values on accounts and products on demand. Defaults for purchase
and sales taxes can be set at independent times. During the transition,
the old taxes can still be selected manually on invoice lines etc.

You can select to also duplicate linked tax code

After the transition, the old taxes can be made inactive.

This module is compatible with OpenERP 7.0

    """,
    'images': ['images/update_tax.png'],
    'depends': ['account'],
    'data': [
        'view/account_tax.xml',
        'view/update_tax_config.xml',
        'view/select_taxes.xml',
        'security/ir.model.access.csv',
    ],
    "license": 'AGPL-3',
    "installable": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
