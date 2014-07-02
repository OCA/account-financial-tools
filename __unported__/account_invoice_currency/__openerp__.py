# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP - Account invoice currency
#    Copyright (C) 2004-2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                           Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2013 Joaquin Gutierrez (http://www.gutierrezweb.es)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
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
##############################################################################

{
    'name': "Company currency in invoices",
    'version': "1.0",
    'author': "Zikzakmedia SL",
    'website': "http://www.zikzakmedia.com",
    'category': "Localisation / Accounting",
    'contributors': ['Joaquín Gutierrez'],
    "description": """
This Module adds functional fields to show invoice in the company currency
==========================================================================

Amount Untaxed, Amount Tax and Amount Total invoice fields in the company currency.
These fields are shown in "Other information" tab in invoice form.
    """,
    'license': "AGPL-3",
    'depends': ["account"],
    'data': [
        "account_invoice_view.xml"
    ],
    'installable': False,
    'active': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
