# -*- coding: utf-8 -*-
#
##############################################################################
#
#    Authors: Adrien Peiffer
#    Copyright (c) 2015 Acsone SA/NV (http://www.acsone.eu)
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


def set_reconcile_ref(cr, registry):
    cr.execute("""SELECT id FROM account_move_line where reconcile_partial_id
        is not NULL and reconcile_ref not like 'P/%'""")
    aml_ids = map(lambda x: x[0], cr.fetchall())
    if aml_ids:
        cr.execute("""UPDATE account_move_line SET reconcile_ref='P/'||
            reconcile_ref where id in %s""", (tuple(aml_ids),))
