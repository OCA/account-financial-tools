# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#   Author: Leonardo Pistone
#   Copyright 2014 Camptocamp SA
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
"""Accounting customisation for delayed posting."""

from openerp.osv import fields, orm

from openerp.addons.connector.queue.job import job
from openerp.addons.connector.session import ConnectorSessionHandler


class account_move(orm.Model):

    """We add a field to mark a move for delayed posting."""

    _name = 'account.move'
    _inherit = 'account.move'

    _columns = {
        'to_post': fields.boolean(
            'To Post',
            help='Check this box to mark the move for batch posting'
        ),
    }

    def mark_for_posting(self, cr, uid, ids, context=None):
        """."""
        session_hdl = ConnectorSessionHandler(cr.dbname, uid)
        with session_hdl.session() as session:
            for move_id in ids:
                validate_one_move.delay(session, self._name, move_id)
                print('===== PUT IN QUEUE!!!!! %s' % move_id)
                # work with session


@job
def validate_one_move(session, model_name, move_id):
    """Press the button to validate a move. Return True.

    This trivial function is there just to be called as a job with the delay
    method.

    """
    return session.pool['account.move'].button_validate(
        session.cr,
        session.uid,
        [move_id]
    )
