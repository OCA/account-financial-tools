# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Numérigraphe SARL.
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
    'name': 'French company identity numbers SIRET/SIREN/NIC',
    'version': '1.0',
    "category": 'Accounting',
    'description': '''
This module add the French company identity numbers.
====================================================

This can help any company doing business with French companies
by letting users track the partners' unique identification
numbers from the official SIRENE registry in France: SIRET, SIREN and NIC.
These numbers identify each company and their subsidiaries, and are
often required for administrative tasks.

On the Partner form, users will be able to enter the SIREN
and NIC numbers, and the SIRET number will be calculated
automatically.  The last digits of the SIREN and NIC are control keys:
OpenERP will check their validity when partners are recorded.

ATTENTION! this module replaces the fields on the Company form with the new
ones on the Partner form, but it will NOT copy the corresponding data: you
will have to enter them again.
''',
    'author': u'Numérigraphe SARL',
    'depends': ['account', 'l10n_fr'],
    'data': [
        'partner_view.xml',
    ],
    'installable': True,
    'active': False,
}
