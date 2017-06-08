# -*- coding: utf-8 -*-
##############################################################################
#
#     This file is part of account_type_multi_company,
#     an Odoo module.
#
#     Copyright (c) 2015 ACSONE SA/NV (<http://acsone.eu>)
#     Copyright (c) 2015 Noviat (<http://acsone.eu>)
#
#     account_type_multi_company is free software:
#     you can redistribute it and/or modify it under the terms of the GNU
#     Affero General Public License as published by the Free Software
#     Foundation,either version 3 of the License, or (at your option) any
#     later version.
#
#     account_type_multi_company is distributed
#     in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
#     even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#     PURPOSE.  See the GNU Affero General Public License for more details.
#
#     You should have received a copy of the GNU Affero General Public License
#     along with account_type_multi_company.
#     If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "Multi company account types",
    'summary': """
        Make account types multi-company aware""",
    'author': "ACSONE SA/NV,"
              "Noviat,"
              "Odoo Community Association (OCA)",
    'category': 'Accounting & Finance',
    'version': '8.0.1.0',
    'license': 'AGPL-3',
    'depends': [
        'account',
    ],
    'data': [
        'security/multi_company.xml',
        'views/account_type.xml',
    ],
}
