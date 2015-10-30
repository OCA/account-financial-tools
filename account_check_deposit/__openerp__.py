# -*- coding: utf-8 -*-
###############################################################################
#
#   account_check_deposit for Odoo
#   Copyright (C) 2012-2015 Akretion (http://www.akretion.com/)
#   @author: Benoît GUILLOT <benoit.guillot@akretion.com>
#   @author: Chafique DELLI <chafique.delli@akretion.com>
#   @author: Alexis de Lattre <alexis.delattre@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

{
    'name': 'Account Check Deposit',
    'version': '8.0.0.1.0',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Manage deposit of checks to the bank',
    'author': "Akretion,Odoo Community Association (OCA)",
    'website': 'http://www.akretion.com/',
    'depends': [
        'account_accountant',
        'report_webkit',
    ],
    'data': [
        'views/account_deposit_view.xml',
        'views/account_move_line_view.xml',
        'data/account_deposit_sequence.xml',
        'views/company_view.xml',
        'security/ir.model.access.csv',
        'security/check_deposit_security.xml',
        'data/account_data.xml',
        'report/report.xml',
        'report/report_checkdeposit.xml',
    ],
    'installable': True,
    'application': True,
}
