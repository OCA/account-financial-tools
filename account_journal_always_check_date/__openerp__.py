# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account Journal Always Check Date module for OpenERP
#    Copyright (C) 2013-2014 Akretion (http://www.akretion.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
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
    'name': 'Account Journal Always Check Date',
    'version': '8.0.0.1.0',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Option Check Date in Period always active on journals',
    'description': """
Check Date in Period always active on Account Journals
======================================================

This module:

* activates the 'Check Date in Period' option on all existing account journals,

* enable the 'Check Date in Period' option on new account journals,

* prevent users from deactivating the 'Check Date in Period' option.

So this module is an additionnal security for countries where, on an account
move, the date must be inside the period.

Please contact Alexis de Lattre from Akretion <alexis.delattre@akretion.com>
for any help or question about this module.
    """,
    'author': "Akretion,Odoo Community Association (OCA)",
    'website': 'http://www.akretion.com',
    'depends': ['account'],
    'data': [],
    'installable': True,
    'active': False,
}
