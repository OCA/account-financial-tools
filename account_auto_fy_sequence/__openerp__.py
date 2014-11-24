# coding=utf-8
##############################################################################
#
#    account_auto_fy_sequence module for Odoo
#    Copyright (C) 2014 ACSONE SA/NV (<http://acsone.eu>)
#    @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
#
#    account_auto_fy_sequence is free software:
#    you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License v3 or later
#    as published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    account_auto_fy_sequence is distributed
#    in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License v3 or later for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    v3 or later along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Automatic Fiscal Year Sequences',
    'version': '0.1',
    'category': 'Accounting',
    'description': """
    Automatic creation of fiscal year sequences.

    This modules adds the possibility to use the %(fy)s placeholder
    in sequences. %(fy)s is replaced by the fiscal year code when
    using the sequence.

    The first time the sequence is used for a given fiscal year,
    a specific fiscal year sequence starting at 1 is created automatically.

    /!\ If you change %(year)s to %(fy)s on a sequence that has
    already been used for the current fiscal year, make sure to manually
    create the fiscal year sequence for the current fiscal year and
    initialize it's next number to the correct value.
    """,
    'author': 'ACSONE SA/NV',
    'website': 'http://acsone.eu',
    'depends': ['account'],
    'data': ['views/ir_sequence_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
