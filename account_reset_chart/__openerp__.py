# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, an open source suite of business apps
#    This module copyright (C) 2014 Therp BV (<http://therp.nl>).
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
    "name": "Reset a chart of accounts",
    "version": "1.0",
    "author": "Therp BV",
    "category": 'Partner',
    "description": """
Removes the current chart of accounts, including moves and journals. By
necessity, this process also removes the company's bank accounts as they
are linked to the company's journals and the company's payment orders
and payment modes if the payment module is installed.

No interface is provided. Please run through xmlrpc, for instance using
erppeek:


import erppeek

host = 'localhost'
port = '8069'
user_pw = 'admin'
dbname = 'openerp'

client = erppeek.Client('http://%s:%s' % (host, port))
client.login('admin', user_pw, dbname)
wiz_id = client.create('account.reset.chart', {'company_id': 1})
client.AccountResetChart.reset_chart([wiz_id])


Use with caution, obviously.

Compatibility
=============
This module is compatible with Odoo 7.0.
""",
    "depends": [
        'account',
    ],
}
