# -*- coding: utf-8 -*-
##############################################################################
#
#     This file is part of account_move_reconcile_helper,
#     an Odoo module.
#
#     Copyright (c) 2015 ACSONE SA/NV (<http://acsone.eu>)
#
#     account_move_reconcile_helper is free software:
#     you can redistribute it and/or modify it under the terms of the GNU
#     Affero General Public License as published by the Free Software
#     Foundation,either version 3 of the License, or (at your option) any
#     later version.
#
#     account_move_reconcile_helper is distributed
#     in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
#     even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#     PURPOSE.  See the GNU Affero General Public License for more details.
#
#     You should have received a copy of the GNU Affero General Public License
#     along with account_move_reconcile_helper.
#     If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "Account Move Reconcile Helper",
    'author': "ACSONE SA/NV,Odoo Community Association (OCA)",
    'website': "http://acsone.eu",
    'category': 'Accounting & Finance',
    'version': '0.1',
    'license': 'AGPL-3',
    'depends': [
        'web',
        'web_option_auto_color',
        'account',
    ],
    'data': [
        'views/account_move_line_view.xml',
    ],
}
