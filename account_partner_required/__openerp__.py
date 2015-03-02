# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account partner required module for OpenERP
#    Copyright (C) 2014 Acsone (http://acsone.eu).
#    @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
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
    'name': 'Account partner required',
    'version': '0.1',
    'category': 'Generic Modules/Accounting',
    'license': 'AGPL-3',
    'description': """This module adds an option "partner policy"
on account types.

You have the choice between 3 policies : optional (the default),
always (require a partner), and never (forbid a partner).

This module is useful to enforce a partner on account move lines on
customer and supplier accounts.

Module developed by Stéphane Bidoul <stephane.bidoul@acsone.eu>,
inspired by Alexis de Lattre <alexis.delattre@akretion.com>'s
account_analytic_required module.
""",
    'author': "ACSONE SA/NV,Odoo Community Association (OCA)",
    'website': 'http://acsone.eu/',
    'depends': ['account'],
    'data': ['account_view.xml'],
    'installable': True,
}
