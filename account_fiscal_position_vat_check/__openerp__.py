# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account Fiscal Position VAT Check module for Odoo
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
    'name': 'Account Fiscal Position VAT Check',
    'version': '8.0.0.1.1',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Check VAT on invoice validation',
    'description': """
Check that the Customer has a VAT number on invoice validation
==============================================================

This module adds an option **Customer must have VAT** on fiscal positions.
When a user tries to validate a customer invoice or refund
with a fiscal position that have this option, OpenERP will check that
the customer has a VAT number.

If it doesn't, OpenERP will block the validation of the invoice
and display an error message.

In the European Union (EU), when an EU company sends an invoice to
another EU company in another country, it can invoice without VAT
(most of the time) but the VAT number of the customer must be displayed
on the invoice.

This module also displays a warning when a user sets
a fiscal position with the option **Customer must have VAT** on a customer
and this customer doesn't have a VAT number in OpenERP yet.

Please contact Alexis de Lattre from Akretion <alexis.delattre@akretion.com>
for any help or question about this module.
    """,
    'author': "Akretion,Odoo Community Association (OCA)",
    'website': 'http://www.akretion.com',
    'depends': ['account', 'base_vat'],
    'data': [
        'account_fiscal_position_view.xml',
        'partner_view.xml',
    ],
    'installable': True,
}
