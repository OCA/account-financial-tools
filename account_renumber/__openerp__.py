# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP - Account renumber wizard
#    Copyright (C) 2009 Pexego Sistemas Informáticos. All Rights Reserved
#    Copyright (c) 2013 Servicios Tecnológicos Avanzados
#                       (http://www.serviciosbaeza.com)
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
    'version': "8.0.1.0.0",
    'author': "Pexego,Odoo Community Association (OCA)",
    'website': "http://www.pexego.es",
    'category': "Accounting & Finance",
    'contributors': ['Pedro M. Baeza', 'Jordi Llinares', 'Joaquín Gutierrez'],
    'description': """
This module adds a wizard to renumber account moves by date only for admin.
===========================================================================

The wizard, which is accesible from the "End of Period" menuitem,
lets you select journals, periods, and a starting number. When
launched, it renumbers all posted moves that match selected criteria
(after ordering them by date).

It will recreate the sequence number for each account move
using its journal sequence, which means that:
    - Sequences per journal are supported.
    - Sequences with prefixes and suffixes based on the move
      date are also supported.
            """,
    "license": "AGPL-3",
    "depends": [
        'account',
    ],
    "demo": [],
    "data": [
        'wizard/wizard_renumber_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
