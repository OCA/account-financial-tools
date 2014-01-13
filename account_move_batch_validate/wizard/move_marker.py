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
"""Wizards for batch posting."""

from openerp.osv import fields, orm


class AccountMoveMarker(orm.TransientModel):

    """Wizard to mark account moves for batch posting."""

    _name = "account.move.marker"
    _inherit = "account.common.report"
    _description = "Mark Journal Items for batch posting"

    _columns = {
        'action': fields.selection([
            ('mark', 'Mark for posting'),
            ('unmark', 'Unmark for posting'),
        ], "Action", required=True),

    }

    _defaults = {
        'action': 'mark',
    }

    def button_mark(self, cr, uid, ids, context=None):
        """Mark/unmark lines and update the queue. Return action."""

        for wiz in self.browse(cr, uid, ids, context=context):

            move_obj = self.pool['account.move']

            if wiz.action == 'mark':
                domain = []
                if wiz.journal_ids:
                    domain.append((
                        'journal_id',
                        'in',
                        [journal.id for journal in wiz.journal_ids]
                    ))

                move_ids = move_obj.search(cr, uid, domain, context=context)

                move_obj.mark_for_posting(cr, uid, move_ids, context=context)

                return {'type': 'ir.actions.act_window_close'}

            elif wiz.action == 'unmark':
                # TODO
                raise NotImplementedError(
                    'The Unmark action is not implemented yet'
                )
            if wiz.filter != 'filter_no':
                # TODO
                raise NotImplementedError(
                    'Date and period filter are not implemented yet'
                )
