# -*- encoding: utf-8 -*-
##############################################################################
#
#    Currency rate date check module for Odoo
#    Copyright (C) 2012-2014 Akretion (http://www.akretion.com).
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
    'name': 'Currency Rate Date Check',
    'version': '8.0.1.0.0',
    'category': 'Financial Management/Configuration',
    'license': 'AGPL-3',
    'summary': "Make sure currency rates used are always up-to-update",
    'description': """
Currency Rate Date Check
========================

This module adds a check on dates when doing currency conversion in Odoo.
It checks that the currency rate used to make the conversion
is not more than N days away from the date of the amount to convert.

The maximum number of days of the interval can be
configured on the company form.

Please contact Alexis de Lattre from Akretion <alexis.delattre@akretion.com>
for any help or question about this module.
    """,
    'author': "Akretion,Odoo Community Association (OCA)",
    'website': 'http://www.akretion.com',
    'depends': ['base'],
    'data': ['company_view.xml'],
    'images': [
        'images/date_check_error_popup.jpg',
        'images/date_check_company_config.jpg',
        ],
    'installable': True,
}
