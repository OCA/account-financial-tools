# -*- coding: utf-8 -*-
##############################################################################
#
#     This file is part of account_filter_payable_receivable, an Odoo module.
#
#     Copyright (c) 2015 ACSONE SA/NV (<http://acsone.eu>)
#
#     account_filter_payable_receivable is free software: you can redistribute
#     it and/or modify it under the terms of the GNU Affero General
#     Public License as published by the Free Software Foundation, either
#     version 3 of the License, or (at your option) any later version.
#
#     account_filter_payable_receivable is distributed in the hope that it will
#     be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.
#
#     You should have received a copy of the
#     GNU Affero General Public License
#     along with account_filter_payable_receivable.
#     If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "Account Filter Payable Receivable",

    'summary': """
        Filter your Journal Items per payable and receivable account""",
    'author': "ACSONE SA/NV",
    'website': "http://acsone.eu",
    'category': 'Accounting & Finance',
    'version': '1.0',
    'license': 'AGPL-3',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_move_line_view.xml',
    ],
}
