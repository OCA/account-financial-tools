# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#   account_check_deposit for OpenERP                                         #
#   Copyright (C) 2012 Akretion Benoît GUILLOT <benoit.guillot@akretion.com>  #
#   Copyright (C) 2013 Akretion Chafique DELLI <chafique.delli@akretion.com>  #
#                                                                             #
#   This program is free software: you can redistribute it and/or modify      #
#   it under the terms of the GNU Affero General Public License as            #
#   published by the Free Software Foundation, either version 3 of the        #
#   License, or (at your option) any later version.                           #
#                                                                             #
#   This program is distributed in the hope that it will be useful,           #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#   GNU Affero General Public License for more details.                       #
#                                                                             #
#   You should have received a copy of the GNU Affero General Public License  #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################



{
    'name': 'account_check_deposit',
    'version': '0.1',
    'category': 'Generic Modules/Others',
    'license': 'AGPL-3',
    'description': """This module allows you to use check deposits.
        With a new model : account_check_deposit you can select all
        the checks payments and create a global deposit for the selected checks.
        You may have to create an account for recieved checks and a journal for payment by checks.""",
    'author': 'Akretion',
    'website': 'http://www.akretion.com/',
    'depends': ['account_accountant',
                'report_webkit',
                'sale_quick_payment'
                ],
    'init_xml': [],
    'update_xml': [
           'account_deposit_view.xml',
           'account_deposit_sequence.xml',
           'account_type_data.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
