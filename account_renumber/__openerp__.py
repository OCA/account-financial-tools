# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP - Account renumber wizard
#    Copyright (C) 2009 Pexego Sistemas Informáticos. All Rights Reserved
#    Copyright (c) 2013 Servicios Tecnológicos Avanzados (http://www.serviciosbaeza.com)
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
#    Copyright (c) 2013 Joaquin Gutierrez (http://www.gutierrezweb.es)
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
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
    'name': "Account renumber wizard",
    'version': "1.0",
    'author': "Pexego",
    'website': "http://www.pexego.es",
    'category': "Enterprise Specific Modules",
    'contributors' : ['Pedro M. Baeza', 'Joaquín Gutierrez'],
    'description': """
This module adds a wizard to renumber account moves by date only for admin users.
=================================================================================

The wizard, that will be added to the "End of Year Treatments",
let's you select one or more journals and fiscal periods,
set a starting number; and then renumber all the posted moves
from those journals and periods sorted by date.

It will recreate the sequence number of each account move using their journal sequence so:
    - Sequences per journal are supported.
    - Sequences with prefixes and sufixes based on the move date are also supported.
            """,
    "license" : "AGPL-3",
    "depends" : [
                'account',
    ],
    "demo" : [],
    "data": [
        'wizard/wizard_renumber_view.xml',
    ],
    "active": False,
    'installable': False
}
