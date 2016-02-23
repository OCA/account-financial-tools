# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 ONESTEiN BV (<http://www.onestein.eu>).
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
    'name': 'Costcenter',
    'images': ['static/description/main_screenshot.png'],
    'summary': """Costcenter information for invoice lines""",
    'depends': [
        'account',
    ],
    'author': "ONESTEiN BV",
    'website': 'http://www.onestein.eu',
    'category': 'Accounting',
    'version': '1.2',
    'data': [
        'security/ir.model.access.csv',
        'views/account_cost_center.xml',
        'views/account_move.xml',
        'views/account_move_line.xml',
        'views/account_invoice.xml',
        'views/account_invoice_report.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
